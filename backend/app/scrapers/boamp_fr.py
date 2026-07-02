"""Scraper API BOAMP — marchés publics français (open data DILA)."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
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
    parse_date_iso,
)

logger = logging.getLogger(__name__)

SOURCE_NOM = "BOAMP France"
PAYS = "France"
API_URL = (
    "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
)
DETAIL_URL = "https://www.boamp.fr/pages/avis/?q=idweb:{idweb}"
LOOKBACK_DAYS = 14
PAGE_SIZE = 100
MAX_PAGES = 30
REQUEST_TIMEOUT = 45.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
}


class BoampFrScraper:
    def _parse_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        idweb = record.get("idweb")
        objet = (record.get("objet") or "").strip()
        if not idweb or not objet:
            return None

        organisme = (record.get("nomacheteur") or "Non précisé").strip()
        date_publication = parse_date_iso(record.get("dateparution"))
        date_limite = parse_date_iso(record.get("datelimitereponse"))

        famille = record.get("famille_libelle") or record.get("nature_libelle") or ""
        description = objet
        if famille:
            description = f"{objet}\n{famille}"

        return {
            "titre": objet[:500],
            "organisme": organisme[:200],
            "description": description[:2000],
            "date_publication": date_publication,
            "date_limite": date_limite,
            "lien_source": DETAIL_URL.format(idweb=quote(str(idweb))),
        }

    def run(self) -> dict[str, Any]:
        repo = ScraperRepository()
        source_id: Any = None
        nb_trouvees = 0
        nb_nouvelles = 0

        try:
            source_id = repo.get_source_id(SOURCE_NOM)
            logger.info("Démarrage scraper %s", SOURCE_NOM)

            since = (datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)).strftime(
                "%Y-%m-%d"
            )
            where = f"dateparution >= date'{since}' AND NOT nature='ATTRIBUTION'"

            with httpx.Client(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                trust_env=False,
            ) as http:
                for page in range(1, MAX_PAGES + 1):
                    offset = (page - 1) * PAGE_SIZE
                    params = {
                        "limit": PAGE_SIZE,
                        "offset": offset,
                        "where": where,
                        "order_by": "dateparution DESC",
                    }
                    response = http.get(API_URL, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    results = payload.get("results") or []
                    if not results:
                        break

                    for record in results:
                        item = self._parse_record(record)
                        if not item:
                            continue
                        nb_trouvees += 1
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

                    total = payload.get("total_count")
                    logger.info(
                        "BOAMP page %d : %d enregistrement(s) (total API %s)",
                        page,
                        len(results),
                        total,
                    )
                    if len(results) < PAGE_SIZE:
                        break
                    if total is not None and offset + PAGE_SIZE >= total:
                        break
                    time.sleep(0.3)

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
