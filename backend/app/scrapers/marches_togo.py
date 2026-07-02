"""Scraper pour le portail Marchés Publics du Togo (marchespublicstogo.com)."""

from __future__ import annotations

import logging
import random
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

logger = logging.getLogger(__name__)

SOURCE_NOM = "Marchés Publics Togo"
PAYS = "Togo"
BASE_URL = "https://marchespublicstogo.com"
LISTING_URL = f"{BASE_URL}/consultations"
REQUEST_TIMEOUT = 45.0
DELAY_MIN = 0.8
DELAY_MAX = 1.5
MAX_PAGES = 50

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": BASE_URL,
}


class MarchesTogoScraper:
    def _parse_page(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        offres: list[dict[str, Any]] = []
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            reference = cells[0].get_text(" ", strip=True)
            titre = cells[1].get_text(" ", strip=True)
            if not titre or titre.lower() == "objet":
                continue

            organisme = cells[2].get_text(" ", strip=True) or "Non précisé"
            type_marche = cells[3].get_text(" ", strip=True)
            date_limite = parse_date_flexible(cells[5].get_text()) if len(cells) > 5 else None

            link_el = row.find("a", href=True)
            lien = (
                urljoin(BASE_URL + "/", link_el["href"])
                if link_el
                else LISTING_URL
            )

            label = f"{reference} — {titre}" if reference else titre
            description = titre
            if type_marche and type_marche != "—":
                description = f"{titre} ({type_marche})"

            offres.append(
                {
                    "titre": label[:500],
                    "organisme": organisme,
                    "description": description[:2000],
                    "date_publication": None,
                    "date_limite": date_limite,
                    "lien_source": lien,
                }
            )
        return offres

    def run(self) -> dict[str, Any]:
        repo = ScraperRepository()
        source_id: Any = None
        nb_trouvees = 0
        nb_nouvelles = 0

        try:
            source_id = repo.get_source_id(SOURCE_NOM)
            logger.info("Démarrage scraper %s", SOURCE_NOM)

            parsed: list[dict[str, Any]] = []
            seen_links: set[str] = set()

            with httpx.Client(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                trust_env=False,
            ) as http:
                for page in range(1, MAX_PAGES + 1):
                    if page > 1:
                        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                    url = LISTING_URL if page == 1 else f"{LISTING_URL}?page={page}"
                    response = http.get(url)
                    if response.status_code >= 500:
                        logger.warning("HTTP %d page %d — arrêt", response.status_code, page)
                        break
                    response.raise_for_status()
                    page_items = self._parse_page(response.text)
                    if not page_items:
                        break

                    new_items = 0
                    for item in page_items:
                        if item["lien_source"] in seen_links:
                            continue
                        seen_links.add(item["lien_source"])
                        parsed.append(item)
                        new_items += 1

                    if new_items == 0:
                        break

            if not parsed:
                raise ValueError("Aucune consultation publique trouvée sur marchespublicstogo.com")

            nb_trouvees = len(parsed)
            for item in parsed:
                hash_unique = compute_hash(
                    item["titre"], item["organisme"], item["date_limite"]
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
