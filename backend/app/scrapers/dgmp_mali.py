"""Scraper pour le portail DGMP-DSP Mali (dgmp.gouv.ml)."""

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

SOURCE_NOM = "DGMP Mali"
PAYS = "Mali"
BASE_URL = "https://dgmp.gouv.ml"
LISTING_URL = f"{BASE_URL}/"
REQUEST_TIMEOUT = 45.0
DELAY_MIN = 1.0
DELAY_MAX = 2.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": BASE_URL,
}


class DgmpMaliScraper:
    def _parse_listing(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        offres: list[dict[str, Any]] = []
        seen: set[str] = set()

        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue

                autorite = cells[0].get_text(" ", strip=True)
                service = cells[1].get_text(" ", strip=True)
                libelle = cells[2].get_text(" ", strip=True)
                if not libelle or libelle.lower() == "libellé du dossier":
                    continue

                date_raw = cells[3].get_text(" ", strip=True)
                date_publication = parse_date_flexible(date_raw)

                link_el = row.find("a", href=True)
                lien = (
                    urljoin(BASE_URL + "/", link_el["href"])
                    if link_el
                    else LISTING_URL
                )

                organisme = autorite or service or "Non précisé"
                key = f"{libelle}|{organisme}|{date_raw}"
                if key in seen:
                    continue
                seen.add(key)

                titre = libelle[:500]
                if service and service != autorite:
                    description = f"{libelle}\n{service}"
                else:
                    description = libelle

                offres.append(
                    {
                        "titre": titre,
                        "organisme": organisme,
                        "description": description[:2000],
                        "date_publication": date_publication,
                        "date_limite": None,
                        "lien_source": lien,
                    }
                )

        if not offres:
            raise ValueError("Aucune offre trouvée sur dgmp.gouv.ml")
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
