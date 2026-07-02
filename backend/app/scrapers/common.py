"""Utilitaires partagés entre les scrapers."""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from app.db.config import settings
from app.models.enums import ScrapingStatus
from app.scrapers.contact import enrich_offre_contact
from app.scrapers.links import lien_is_better

logger = logging.getLogger(__name__)

USER_AGENT = "MarchesPublicsOuest-Bot/0.1 (+scraping; contact: dev@marches-publics-ouest.local)"

MONTHS_FR = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}

MONTHS_EN = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def compute_hash(titre: str, organisme: str, date_pub: datetime | None) -> str:
    date_part = date_pub.strftime("%Y-%m-%d") if date_pub else ""
    payload = f"{titre.strip()}|{organisme.strip()}|{date_part}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_date_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


KNOWN_PAYS = (
    "Bénin",
    "Côte d'Ivoire",
    "Mali",
    "Togo",
    "France",
    "Europe",
    "Afrique du Sud",
)

PAYS_ALIASES: dict[str, str] = {
    "benin": "Bénin",
    "bénin": "Bénin",
    "mali": "Mali",
    "togo": "Togo",
    "cote d'ivoire": "Côte d'Ivoire",
    "côte d'ivoire": "Côte d'Ivoire",
    "cote divoire": "Côte d'Ivoire",
    "ivory coast": "Côte d'Ivoire",
    "france": "France",
    "europe": "Europe",
    "afrique du sud": "Afrique du Sud",
    "south africa": "Afrique du Sud",
}


def normalize_pays_label(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower().replace("´", "'").replace("`", "'")
    if cleaned in PAYS_ALIASES:
        return PAYS_ALIASES[cleaned]
    for pays in KNOWN_PAYS:
        if cleaned == pays.lower():
            return pays
    return None


def infer_pays_from_text(text: str, fallback: str) -> str:
    if not text:
        return fallback

    normalized = text.replace("´", "'").replace("`", "'")
    prefix = re.match(
        r"(?:AAO|AMI|GPN|PPM|EOI|SPN|AOI)\s*-\s*([^-]+?)\s*-",
        normalized,
        re.IGNORECASE,
    )
    if prefix:
        candidate = normalize_pays_label(prefix.group(1))
        if candidate:
            return candidate

    lowered = normalized.lower()
    for alias, pays in sorted(PAYS_ALIASES.items(), key=lambda item: -len(item[0])):
        if alias in lowered:
            return pays

    for pays in KNOWN_PAYS:
        if pays.lower() in lowered:
            return pays

    return fallback


def parse_date_flexible(value: str | None) -> datetime | None:
    """Parse ISO, DD-MM-YYYY, French and English textual dates."""
    if not value:
        return None

    value = value.strip()
    value = re.sub(r"\s+", " ", value)

    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value[:10], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    if " " in value and len(value) >= 10:
        parts = value.split()
        if len(parts) >= 3:
            try:
                day = int(parts[0])
                month_name = parts[1].lower().rstrip(".")
                year = int(parts[2])
                month = MONTHS_FR.get(month_name) or MONTHS_EN.get(month_name)
                if month:
                    return datetime(year, month, day, tzinfo=timezone.utc)
            except ValueError:
                pass

    return None


class ScraperRepository:
    """Accès MongoDB synchrone pour les scrapers."""

    def __init__(self) -> None:
        self._client: MongoClient | None = None

    def get_db(self):
        if self._client is None:
            self._client = MongoClient(settings.mongodb_uri)
        return self._client[settings.mongodb_db_name]

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def get_source_id(self, source_nom: str) -> Any:
        source = self.get_db().sources.find_one({"nom": source_nom})
        if not source:
            raise ValueError(
                f"Source « {source_nom} » introuvable en base. Exécutez seed.py d'abord."
            )
        return source["_id"]

    def insert_offre(self, offre: dict[str, Any]) -> bool:
        doc = enrich_offre_contact(dict(offre))
        try:
            self.get_db().offres.insert_one(doc)
            return True
        except DuplicateKeyError:
            updates: dict[str, Any] = {}
            if doc.get("contact"):
                updates["contact"] = doc["contact"]
            if doc.get("lien_source"):
                existing = self.get_db().offres.find_one(
                    {"hash_unique": doc["hash_unique"]},
                    {"lien_source": 1},
                )
                if existing and lien_is_better(
                    doc["lien_source"],
                    existing.get("lien_source"),
                ):
                    updates["lien_source"] = doc["lien_source"]
            if updates:
                self.get_db().offres.update_one(
                    {"hash_unique": doc["hash_unique"]},
                    {"$set": updates},
                )
            return False

    def log_execution(
        self,
        source_id: Any,
        statut: ScrapingStatus,
        nb_trouvees: int,
        nb_nouvelles: int,
        message_erreur: str | None = None,
    ) -> None:
        self.get_db().logs_scraping.insert_one(
            {
                "source_id": source_id,
                "date_execution": datetime.now(timezone.utc),
                "statut": statut.value,
                "nb_offres_trouvees": nb_trouvees,
                "nb_offres_nouvelles": nb_nouvelles,
                "message_erreur": message_erreur,
            }
        )

    def update_source_execution(self, source_id: Any) -> None:
        self.get_db().sources.update_one(
            {"_id": source_id},
            {"$set": {"derniere_execution": datetime.now(timezone.utc)}},
        )


def build_error_result(
    statut: ScrapingStatus,
    nb_trouvees: int,
    nb_nouvelles: int,
    message: str,
) -> dict[str, Any]:
    return {
        "statut": statut.value,
        "nb_offres_trouvees": nb_trouvees,
        "nb_offres_nouvelles": nb_nouvelles,
        "message_erreur": message,
    }


def build_success_result(nb_trouvees: int, nb_nouvelles: int) -> dict[str, Any]:
    return {
        "statut": ScrapingStatus.SUCCES.value,
        "nb_offres_trouvees": nb_trouvees,
        "nb_offres_nouvelles": nb_nouvelles,
        "message_erreur": None,
    }
