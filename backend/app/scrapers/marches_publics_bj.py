"""Scraper pour le Portail Marchés Publics du Bénin (marches-publics.bj)."""

from __future__ import annotations

import hashlib
import logging
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings
from app.models.enums import ScrapingStatus
from app.scrapers.bj_crypto import build_bj_offre_url
from app.scrapers.contact import contact_from_marches_publics_bj, enrich_offre_contact
from app.scrapers.links import lien_is_better

logger = logging.getLogger(__name__)

USER_AGENT = "MarchesPublicsOuest-Bot/0.1 (+scraping; contact: dev@marches-publics-ouest.local)"
SOURCE_NOM = "Portail Marchés Publics Bénin"
PAYS = "Bénin"
BASE_URL = "https://www.marches-publics.bj"
LISTING_URL = f"{BASE_URL}/appels-doffres"
API_URL = "https://api.marches-publics.bj/v2/api/portail/appelsoffres"
PAGE_SIZE = 20
REQUEST_TIMEOUT = 45.0
DELAY_MIN = 1.0
DELAY_MAX = 2.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Origin": BASE_URL,
    "Referer": LISTING_URL,
}


class MarchesPublicsBjScraper:
    """Récupère les appels d'offres via l'API JSON publique du portail béninois."""

    def __init__(self) -> None:
        self._client: MongoClient | None = None

    def _get_db(self):
        if self._client is None:
            self._client = MongoClient(settings.mongodb_uri)
        return self._client[settings.mongodb_db_name]

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def _get_source_id(self, db) -> Any:
        source = db.sources.find_one({"nom": SOURCE_NOM})
        if not source:
            raise ValueError(
                f"Source « {SOURCE_NOM} » introuvable en base. Exécutez seed.py d'abord."
            )
        return source["_id"]

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _compute_hash(titre: str, organisme: str, date_pub: datetime | None) -> str:
        date_part = date_pub.strftime("%Y-%m-%d") if date_pub else ""
        payload = f"{titre.strip()}|{organisme.strip()}|{date_part}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_lien(dos_id: int | str) -> str:
        return build_bj_offre_url(dos_id)

    @staticmethod
    def _normalize_titre(value: str) -> str:
        return " ".join(value.replace("\n", " ").split())

    def _extract_offre(self, item: dict[str, Any], source_id: Any) -> dict[str, Any] | None:
        appel = item.get("appelsoffres") or {}
        autorite = item.get("autoriteContractante") or {}

        titre = self._normalize_titre(appel.get("apoObjet") or "")
        organisme = (autorite.get("denomination") or autorite.get("sigle") or "").strip()
        dos_id = item.get("dosID")

        if not titre or not organisme or dos_id is None:
            logger.warning("Offre ignorée (champs manquants) : dosID=%s", dos_id)
            return None

        date_publication = self._parse_date(item.get("dosDatePublication"))
        date_limite = self._parse_date(item.get("dosDateLimiteDepot"))
        hash_unique = self._compute_hash(titre, organisme, date_publication)
        description = self._normalize_titre(item.get("dosDescriptif") or titre)
        contact = contact_from_marches_publics_bj(item)
        reference = (item.get("dosReference") or appel.get("apoReference") or "").strip()

        offre = {
            "source_id": source_id,
            "external_id": str(dos_id),
            "reference": reference or None,
            "secteur_id": None,
            "titre": titre,
            "organisme": organisme,
            "pays": PAYS,
            "description": description,
            "contact": contact,
            "date_publication": date_publication,
            "date_limite": date_limite,
            "montant_estime": None,
            "lien_source": self._build_lien(dos_id),
            "hash_unique": hash_unique,
            "date_scraping": datetime.now(timezone.utc),
        }
        return enrich_offre_contact(offre)

    def _fetch_page(self, http: httpx.Client, page: int) -> dict[str, Any]:
        params = {"page": page, "size": PAGE_SIZE, "search": ""}
        response = http.get(API_URL, params=params)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict) or "content" not in data:
            raise ValueError(
                "Structure JSON inattendue : clé « content » absente dans la réponse API"
            )
        return data

    def _log_execution(
        self,
        db,
        source_id: Any,
        statut: ScrapingStatus,
        nb_trouvees: int,
        nb_nouvelles: int,
        message_erreur: str | None = None,
    ) -> None:
        db.logs_scraping.insert_one(
            {
                "source_id": source_id,
                "date_execution": datetime.now(timezone.utc),
                "statut": statut.value,
                "nb_offres_trouvees": nb_trouvees,
                "nb_offres_nouvelles": nb_nouvelles,
                "message_erreur": message_erreur,
            }
        )

    def _upsert_fields(self, offre: dict[str, Any]) -> dict[str, Any]:
        fields = {
            "external_id": offre["external_id"],
            "titre": offre["titre"],
            "organisme": offre["organisme"],
            "description": offre["description"],
            "date_publication": offre["date_publication"],
            "date_limite": offre["date_limite"],
            "lien_source": offre["lien_source"],
            "hash_unique": offre["hash_unique"],
            "date_scraping": offre["date_scraping"],
        }
        if offre.get("reference"):
            fields["reference"] = offre["reference"]
        if offre.get("contact"):
            fields["contact"] = offre["contact"]
        return fields

    def _find_legacy_offre(self, db, offre: dict[str, Any]) -> dict[str, Any] | None:
        source_id = offre["source_id"]
        external_id = offre.get("external_id")
        if not external_id:
            return None
        return db.offres.find_one(
            {
                "source_id": source_id,
                "external_id": {"$exists": False},
                "lien_source": {
                    "$regex": rf"/appels-doffres/{re.escape(external_id)}(?:\?|$)"
                },
            },
            {"_id": 1, "lien_source": 1, "hash_unique": 1},
        )

    def _insert_offre(self, db, offre: dict[str, Any]) -> bool:
        source_id = offre["source_id"]
        external_id = offre.get("external_id")
        if external_id:
            existing = db.offres.find_one(
                {"source_id": source_id, "external_id": external_id},
                {"_id": 1, "lien_source": 1},
            )
            if not existing:
                existing = self._find_legacy_offre(db, offre)
            if existing:
                updates = self._upsert_fields(offre)
                if not lien_is_better(
                    updates["lien_source"],
                    existing.get("lien_source"),
                    url_base=BASE_URL,
                    listing_url=LISTING_URL,
                ):
                    updates.pop("lien_source", None)
                db.offres.update_one({"_id": existing["_id"]}, {"$set": updates})
                return False

        try:
            db.offres.insert_one(offre)
            return True
        except DuplicateKeyError:
            query: dict[str, Any] = {"hash_unique": offre["hash_unique"]}
            legacy = self._find_legacy_offre(db, offre) if external_id else None
            if legacy:
                updates = self._upsert_fields(offre)
                if not lien_is_better(
                    updates["lien_source"],
                    legacy.get("lien_source"),
                    url_base=BASE_URL,
                    listing_url=LISTING_URL,
                ):
                    updates.pop("lien_source", None)
                db.offres.update_one({"_id": legacy["_id"]}, {"$set": updates})
                return False

            updates = {}
            if offre.get("contact"):
                updates["contact"] = offre["contact"]
            if offre.get("lien_source"):
                existing = db.offres.find_one(query, {"lien_source": 1})
                if existing and lien_is_better(
                    offre["lien_source"],
                    existing.get("lien_source"),
                    url_base=BASE_URL,
                    listing_url=LISTING_URL,
                ):
                    updates["lien_source"] = offre["lien_source"]
            if external_id:
                updates["external_id"] = external_id
                for key in ("titre", "organisme", "description", "reference"):
                    if offre.get(key):
                        updates[key] = offre[key]
            if updates:
                db.offres.update_one(query, {"$set": updates})
            return False

    def run(self) -> dict[str, Any]:
        """Exécute le scraping de bout en bout. Ne lève jamais d'exception non gérée."""
        db = self._get_db()
        source_id: Any = None
        nb_trouvees = 0
        nb_nouvelles = 0

        try:
            source_id = self._get_source_id(db)
            logger.info("Démarrage scraper %s", SOURCE_NOM)

            with httpx.Client(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                trust_env=False,
            ) as http:
                first_page = self._fetch_page(http, page=0)
                total_pages = int(first_page.get("totalPages") or 1)
                nb_trouvees = int(first_page.get("totalElements") or 0)
                logger.info("%d offre(s) trouvée(s) sur %d page(s)", nb_trouvees, total_pages)

                pages_data = [first_page]
                for page in range(1, total_pages):
                    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                    pages_data.append(self._fetch_page(http, page=page))

            for page_data in pages_data:
                for item in page_data.get("content") or []:
                    if not isinstance(item, dict):
                        continue
                    offre = self._extract_offre(item, source_id)
                    if offre and self._insert_offre(db, offre):
                        nb_nouvelles += 1

            db.sources.update_one(
                {"_id": source_id},
                {"$set": {"derniere_execution": datetime.now(timezone.utc)}},
            )
            self._log_execution(
                db, source_id, ScrapingStatus.SUCCES, nb_trouvees, nb_nouvelles
            )
            logger.info(
                "Scraping terminé : %d trouvée(s), %d nouvelle(s)",
                nb_trouvees,
                nb_nouvelles,
            )
            return {
                "statut": ScrapingStatus.SUCCES.value,
                "nb_offres_trouvees": nb_trouvees,
                "nb_offres_nouvelles": nb_nouvelles,
                "message_erreur": None,
            }

        except httpx.TimeoutException as exc:
            msg = f"Timeout réseau après {REQUEST_TIMEOUT}s : {exc}"
            logger.error(msg)
            if source_id:
                self._log_execution(
                    db, source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return {
                "statut": ScrapingStatus.ECHEC.value,
                "nb_offres_trouvees": nb_trouvees,
                "nb_offres_nouvelles": nb_nouvelles,
                "message_erreur": msg,
            }

        except httpx.ConnectError as exc:
            msg = f"Site inaccessible (connexion impossible) : {exc}"
            logger.error(msg)
            if source_id:
                self._log_execution(
                    db, source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return {
                "statut": ScrapingStatus.ECHEC.value,
                "nb_offres_trouvees": nb_trouvees,
                "nb_offres_nouvelles": nb_nouvelles,
                "message_erreur": msg,
            }

        except httpx.HTTPStatusError as exc:
            msg = f"Erreur HTTP {exc.response.status_code} : {exc}"
            logger.error(msg)
            if source_id:
                self._log_execution(
                    db, source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return {
                "statut": ScrapingStatus.ECHEC.value,
                "nb_offres_trouvees": nb_trouvees,
                "nb_offres_nouvelles": nb_nouvelles,
                "message_erreur": msg,
            }

        except ValueError as exc:
            msg = f"Structure de données inattendue : {exc}"
            logger.error(msg)
            if source_id:
                self._log_execution(
                    db, source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return {
                "statut": ScrapingStatus.ECHEC.value,
                "nb_offres_trouvees": nb_trouvees,
                "nb_offres_nouvelles": nb_nouvelles,
                "message_erreur": msg,
            }

        except Exception as exc:
            msg = f"Erreur inattendue ({type(exc).__name__}) : {exc}"
            logger.error(msg, exc_info=True)
            if source_id:
                self._log_execution(
                    db, source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return {
                "statut": ScrapingStatus.ECHEC.value,
                "nb_offres_trouvees": nb_trouvees,
                "nb_offres_nouvelles": nb_nouvelles,
                "message_erreur": msg,
            }

        finally:
            self.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    result = MarchesPublicsBjScraper().run()
    print(
        f"Statut          : {result['statut']}\n"
        f"Offres trouvées : {result['nb_offres_trouvees']}\n"
        f"Nouvelles offres: {result['nb_offres_nouvelles']}"
    )
    if result["message_erreur"]:
        print(f"Erreur          : {result['message_erreur']}")
    return 0 if result["statut"] == ScrapingStatus.SUCCES.value else 1


if __name__ == "__main__":
    sys.exit(main())
