"""Scraper pour le portail DGMP Côte d'Ivoire (marchespublics.ci)."""

from __future__ import annotations

import logging
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.models.enums import ScrapingStatus
from app.scrapers.common import (
    USER_AGENT,
    ScraperRepository,
    build_error_result,
    build_success_result,
    compute_hash,
    parse_date_flexible,
)
from app.scrapers.links import resolve_lien_source

logger = logging.getLogger(__name__)

SOURCE_NOM = "DGMP Côte d'Ivoire"
PAYS = "Côte d'Ivoire"
BASE_URL = "https://marchespublics.ci"
LISTING_URL = f"{BASE_URL}/appel_offre"
REQUEST_TIMEOUT = 45.0
DELAY_MIN = 1.0
DELAY_MAX = 2.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": BASE_URL,
}

_INVALID_DATE = re.compile(r"0001|^-+$")


def _split_objet_organisme(raw: str) -> tuple[str, str]:
    lines = [line.strip() for line in raw.replace("\r", "\n").split("\n") if line.strip()]
    if not lines:
        return "", "Non précisé"
    if len(lines) == 1:
        return lines[0], "Non précisé"
    return lines[0], lines[-1]


def _parse_date_cell(value: str) -> datetime | None:
    cleaned = value.strip()
    if not cleaned or _INVALID_DATE.search(cleaned):
        return None
    return parse_date_flexible(cleaned.replace(" ", ""))


class MarchesPublicsCiScraper:
    def _parse_listing(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            raise ValueError("Structure HTML introuvable : tableau des appels d'offres absent")

        offres: list[dict[str, Any]] = []
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 6:
                continue

            numero = cells[0].get_text(" ", strip=True)
            type_marche = cells[1].get_text(" ", strip=True)
            objet_raw = cells[2].get_text("\n", strip=True)
            titre, organisme = _split_objet_organisme(objet_raw)
            if not titre:
                continue

            date_publication = _parse_date_cell(cells[4].get_text())
            date_limite = _parse_date_cell(cells[5].get_text())
            label = f"{numero} — {titre}" if numero else titre

            link_el = row.find("a", href=True)
            raw_lien = urljoin(f"{BASE_URL}/", link_el["href"]) if link_el else ""
            lien = resolve_lien_source(
                raw_lien,
                url_base=BASE_URL,
                listing_url=LISTING_URL,
            )

            offres.append(
                {
                    "titre": label[:500],
                    "organisme": organisme or "Non précisé",
                    "description": objet_raw[:2000],
                    "date_publication": date_publication,
                    "date_limite": date_limite,
                    "lien_source": lien,
                    "type_marche": type_marche,
                }
            )

        if not offres:
            raise ValueError("Aucune offre trouvée dans le tableau DGMP CI")
        return offres

    def run(self) -> dict[str, Any]:
        repo = ScraperRepository()
        source_id: Any = None
        nb_trouvees = 0
        nb_nouvelles = 0

        try:
            source_id = repo.get_source_id(SOURCE_NOM)
            logger.info("Démarrage scraper %s", SOURCE_NOM)

            with httpx.Client(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                trust_env=False,
            ) as http:
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                response = http.get(LISTING_URL)
                response.raise_for_status()
                parsed = self._parse_listing(response.text)

            nb_trouvees = len(parsed)
            for item in parsed:
                hash_unique = compute_hash(
                    item["titre"], item["organisme"], item["date_publication"]
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

            repo.update_source_execution(source_id)
            repo.log_execution(
                source_id, ScrapingStatus.SUCCES, nb_trouvees, nb_nouvelles
            )
            return build_success_result(nb_trouvees, nb_nouvelles)

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
