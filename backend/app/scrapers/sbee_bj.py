"""Scraper HTML pour SBEE Bénin (marches-publics.sbee.bj)."""

from __future__ import annotations

import logging
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

SOURCE_NOM = "SBEE Bénin"
PAYS = "Bénin"
ORGANISME = "SBEE (Société Béninoise d'Énergie Électrique)"
BASE_URL = "https://marches-publics.sbee.bj"
LISTING_URL = f"{BASE_URL}/appels-doffres"
REQUEST_TIMEOUT = 45.0
DELAY_MIN = 1.0
DELAY_MAX = 2.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": BASE_URL,
}


class SbeeBjScraper:
    """Scrape les appels d'offres SBEE depuis le HTML server-side rendu."""

    def __init__(self) -> None:
        self._repo = ScraperRepository()

    def _parse_listing(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all("div", class_="col-md-12 blog-item")
        if not items:
            raise ValueError(
                "Structure HTML introuvable : aucun bloc « col-md-12 blog-item »"
            )

        offres: list[dict[str, Any]] = []
        for item in items:
            h3 = item.find("h3")
            titre = h3.get_text(strip=True) if h3 else ""
            if not titre:
                logger.warning("Offre SBEE ignorée : titre manquant")
                continue

            desc_el = item.find("p", class_=re.compile(r"job-details"))
            description = desc_el.get_text(strip=True) if desc_el else titre

            date_publication = None
            date_limite = None
            for block in item.find_all("div", class_="dateOffre"):
                label = block.find("strong")
                value = block.get_text("\n", strip=True)
                if label and "publication" in label.get_text(strip=True).lower():
                    raw = value.split("\n")[-1].strip()
                    date_publication = parse_date_flexible(raw)
                elif label and "limite" in label.get_text(strip=True).lower():
                    raw = value.split("\n")[-1].strip()
                    date_limite = parse_date_flexible(raw)

            dossier_link = item.find("a", href=re.compile(r"demande-dossier/appel-doffre/\d+"))
            if dossier_link:
                lien = dossier_link["href"]
            else:
                pdf_link = item.find("a", href=re.compile(r"/uploads/.*\.pdf", re.I))
                lien = pdf_link["href"] if pdf_link else LISTING_URL

            if not lien.startswith("http"):
                lien = f"{BASE_URL}/{lien.lstrip('/')}"

            offres.append(
                {
                    "titre": titre,
                    "organisme": ORGANISME,
                    "description": description,
                    "date_publication": date_publication,
                    "date_limite": date_limite,
                    "lien_source": lien,
                }
            )

        return offres

    def run(self) -> dict[str, Any]:
        source_id: Any = None
        nb_trouvees = 0
        nb_nouvelles = 0

        try:
            source_id = self._repo.get_source_id(SOURCE_NOM)
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
            logger.info("%d offre(s) trouvée(s)", nb_trouvees)

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
                if self._repo.insert_offre(offre):
                    nb_nouvelles += 1

            self._repo.update_source_execution(source_id)
            self._repo.log_execution(
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
                self._repo.log_execution(
                    source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except httpx.ConnectError as exc:
            msg = f"Site inaccessible (connexion impossible) : {exc}"
            logger.error(msg)
            if source_id:
                self._repo.log_execution(
                    source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except httpx.HTTPStatusError as exc:
            msg = f"Erreur HTTP {exc.response.status_code} : {exc}"
            logger.error(msg)
            if source_id:
                self._repo.log_execution(
                    source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except ValueError as exc:
            msg = f"Structure de données inattendue : {exc}"
            logger.error(msg)
            if source_id:
                self._repo.log_execution(
                    source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except Exception as exc:
            msg = f"Erreur inattendue ({type(exc).__name__}) : {exc}"
            logger.error(msg, exc_info=True)
            if source_id:
                self._repo.log_execution(
                    source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
                )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        finally:
            self._repo.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    result = SbeeBjScraper().run()
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
