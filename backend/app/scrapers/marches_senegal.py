"""Scraper API pour le portail officiel APPEL Sénégal (achatspublics.sn)."""

from __future__ import annotations

import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings
from app.models.enums import ScrapingStatus
from app.scrapers.common import (
    USER_AGENT,
    ScraperRepository,
    build_error_result,
    build_success_result,
    compute_hash,
)

logger = logging.getLogger(__name__)

SOURCE_NOM = "Portail Marchés Publics Sénégal"
PAYS = "Sénégal"
BASE_URL = "https://www.achatspublics.sn"
API_URL = "https://api.achatspublics.sn/anon/tdo"
LISTING_URL = f"{BASE_URL}/consultations/tenders"
REQUEST_TIMEOUT = 45.0
DELAY_MIN = 0.5
DELAY_MAX = 1.2
PAGE_SIZE = 50
MAX_PAGES = settings.senegal_max_pages or 0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": BASE_URL,
}


def _parse_api_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _is_test_tender(item: dict[str, Any]) -> bool:
    org = item.get("organization") or {}
    org_name = str(org.get("name") or org.get("libelle") or "")
    libelle = str(item.get("libelle") or "")
    if "TEST" in org_name.upper():
        return True
    return libelle.strip().lower().startswith("[marché de test")


def _map_tender(item: dict[str, Any]) -> dict[str, Any] | None:
    uid = item.get("uid")
    if not uid:
        return None

    if item.get("status") and item["status"] != "PUBLISHED":
        return None
    if _is_test_tender(item):
        return None

    org = item.get("organization") or {}
    organisme = org.get("name") or org.get("libelle") or "Non précisé"
    reference = str(item.get("reference") or "").strip()
    libelle = str(item.get("libelle") or reference or "Sans titre").strip()
    titre = f"{reference} — {libelle}" if reference and reference not in libelle else libelle

    passation = (item.get("passationMode") or {}).get("libelle")
    market_type = (item.get("marketType") or {}).get("libelle")
    description_parts = [p for p in (passation, market_type, item.get("description")) if p]
    description = " · ".join(str(p) for p in description_parts) or libelle

    date_publication = _parse_api_datetime(item.get("publicationDate"))
    date_limite = _parse_api_datetime(item.get("submissionDate"))

    return {
        "titre": titre[:500],
        "organisme": str(organisme)[:300],
        "description": str(description)[:2000],
        "date_publication": date_publication,
        "date_limite": date_limite,
        "lien_source": f"{BASE_URL}/consultations/tenders/{uid}",
        "reference": reference,
    }


class MarchesSenegalScraper:
    """Collecte les appels d'offres via l'API publique anonyme d'APPEL."""

    def _fetch_page(self, http: httpx.Client, page: int) -> dict[str, Any]:
        response = http.get(
            API_URL,
            params={"page": page, "size": PAGE_SIZE},
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            raise ValueError(payload.get("message") or "Réponse API invalide")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("Structure API inattendue : champ data absent")
        return data

    def run(self) -> dict[str, Any]:
        repo = ScraperRepository()
        source_id: Any = None
        nb_trouvees = 0
        nb_nouvelles = 0

        try:
            source_id = repo.get_source_id(SOURCE_NOM)
            logger.info("Démarrage scraper %s", SOURCE_NOM)

            seen_uids: set[str] = set()

            with httpx.Client(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                trust_env=False,
            ) as http:
                page = 0
                while True:
                    if page > 0:
                        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                    if MAX_PAGES and page >= MAX_PAGES:
                        logger.info("Limite de pages atteinte (%d)", MAX_PAGES)
                        break

                    data = self._fetch_page(http, page)
                    content = data.get("content") or []
                    if not content:
                        logger.info("Page %d vide — fin de pagination", page)
                        break

                    for raw in content:
                        uid = raw.get("uid")
                        if not uid or uid in seen_uids:
                            continue
                        seen_uids.add(uid)

                        item = _map_tender(raw)
                        if not item:
                            continue

                        nb_trouvees += 1
                        hash_unique = compute_hash(
                            item["reference"] or item["titre"],
                            item["organisme"],
                            item["date_publication"],
                        )
                        offre = {
                            "source_id": source_id,
                            "secteur_id": None,
                            "titre": item["titre"],
                            "organisme": item["organisme"],
                            "pays": PAYS,
                            "description": item["description"],
                            "date_publication": item["date_publication"],
                            "date_limite": item["date_limite"],
                            "montant_estime": None,
                            "lien_source": item["lien_source"],
                            "hash_unique": hash_unique,
                            "date_scraping": datetime.now(timezone.utc),
                        }
                        if repo.insert_offre(offre):
                            nb_nouvelles += 1

                    logger.info(
                        "Page %d : %d appel(s) API, %d nouvelle(s) offre(s) (total %d)",
                        page,
                        len(content),
                        nb_nouvelles,
                        nb_trouvees,
                    )

                    if data.get("last", True):
                        break
                    page += 1

            repo.update_source_execution(source_id)
            repo.log_execution(
                source_id, ScrapingStatus.SUCCES, nb_trouvees, nb_nouvelles
            )
            logger.info(
                "Scraping terminé : %d trouvée(s), %d nouvelle(s)",
                nb_trouvees,
                nb_nouvelles,
            )
            return build_success_result(nb_trouvees, nb_nouvelles)

        except httpx.TimeoutException as exc:
            msg = f"Timeout réseau après {REQUEST_TIMEOUT}s : {exc}"
            logger.error(msg)
            if source_id:
                repo.log_execution(
                    source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except httpx.HTTPStatusError as exc:
            msg = f"Erreur HTTP {exc.response.status_code} : {exc}"
            logger.error(msg)
            if source_id:
                repo.log_execution(
                    source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except Exception as exc:
            msg = f"Erreur ({type(exc).__name__}) : {exc}"
            logger.error(msg, exc_info=True)
            if source_id:
                repo.log_execution(
                    source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        finally:
            repo.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    result = MarchesSenegalScraper().run()
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
