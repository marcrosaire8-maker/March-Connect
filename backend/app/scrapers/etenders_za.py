"""Scraper API OCDS — eTenders Afrique du Sud (National Treasury)."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

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
    parse_date_flexible,
    parse_date_iso,
)

logger = logging.getLogger(__name__)

SOURCE_NOM = "eTenders Afrique du Sud"
PAYS = "Afrique du Sud"
API_URL = "https://ocds-api.etenders.gov.za/api/OCDSReleases"
PORTAL_URL = "https://www.etenders.gov.za/Home/TenderOpportunities"
LOOKBACK_DAYS = 14
PAGE_SIZE = 100
MAX_PAGES = 50
REQUEST_TIMEOUT = 45.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}


def _parse_release(release: dict[str, Any]) -> dict[str, Any] | None:
    tender = release.get("tender") or {}
    if tender.get("status") not in (None, "active", "planned"):
        return None

    titre = (tender.get("title") or tender.get("description") or "").strip()
    if not titre:
        return None

    buyer = release.get("buyer") or tender.get("procuringEntity") or {}
    organisme = (buyer.get("name") or "Non précisé").strip()

    date_publication = parse_date_iso((release.get("date") or "")[:10])
    period = tender.get("tenderPeriod") or {}
    date_limite = parse_date_flexible((period.get("endDate") or "")[:10])

    description = (tender.get("description") or titre).strip()
    category = tender.get("category") or tender.get("mainProcurementCategory")
    if category:
        description = f"{description}\n{category}"

    lien_source = PORTAL_URL
    documents = tender.get("documents") or []
    for doc in documents:
        url = doc.get("url")
        if url and str(url).startswith("http"):
            lien_source = url
            break

    tender_id = tender.get("id")
    if tender_id and lien_source == PORTAL_URL:
        lien_source = f"https://www.etenders.gov.za/Home/TenderOpportunities?id={tender_id}"

    return {
        "titre": titre[:500],
        "organisme": organisme[:200],
        "description": description[:2000],
        "date_publication": date_publication,
        "date_limite": date_limite,
        "lien_source": lien_source,
    }


class EtendersZaScraper:
    def run(self) -> dict[str, Any]:
        repo = ScraperRepository()
        source_id: Any = None
        nb_trouvees = 0
        nb_nouvelles = 0

        try:
            source_id = repo.get_source_id(SOURCE_NOM)
            logger.info("Démarrage scraper %s", SOURCE_NOM)

            today = datetime.now(timezone.utc).date()
            date_from = (today - timedelta(days=LOOKBACK_DAYS)).isoformat()
            date_to = today.isoformat()

            with httpx.Client(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                trust_env=False,
            ) as http:
                for page in range(1, MAX_PAGES + 1):
                    params = {
                        "PageNumber": page,
                        "PageSize": PAGE_SIZE,
                        "dateFrom": date_from,
                        "dateTo": date_to,
                    }
                    response = http.get(API_URL, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    releases = payload.get("releases") or []
                    if not releases:
                        break

                    for release in releases:
                        item = _parse_release(release)
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

                    logger.info(
                        "eTenders ZA page %d : %d release(s)",
                        page,
                        len(releases),
                    )
                    if len(releases) < PAGE_SIZE:
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
