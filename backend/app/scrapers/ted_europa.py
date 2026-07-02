"""Scraper API TED — appels d'offres publics européens."""

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
)

logger = logging.getLogger(__name__)

SOURCE_NOM = "TED Europe"
PAYS = "Europe"
API_URL = "https://api.ted.europa.eu/v3/notices/search"
DETAIL_URL = "https://ted.europa.eu/fr/notice/-/detail/{nd}"
LOOKBACK_DAYS = 14
PAGE_SIZE = 100
MAX_PAGES = 40
REQUEST_TIMEOUT = 60.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def _pick_title(ti: dict[str, str] | None) -> str:
    if not ti:
        return ""
    for lang in ("fra", "eng", "deu", "spa", "ita", "nld", "por"):
        if ti.get(lang):
            return ti[lang].strip()
    return next(iter(ti.values()), "").strip()


def _pick_buyer(buyer: dict[str, list[str]] | str | None) -> str:
    if isinstance(buyer, str):
        return buyer.strip()
    if isinstance(buyer, dict):
        for lang in ("fra", "eng", "deu"):
            names = buyer.get(lang)
            if names:
                return names[0].strip()
        for names in buyer.values():
            if names:
                return names[0].strip()
    return "Non précisé"


class TedEuropaScraper:
    def _parse_notice(self, notice: dict[str, Any]) -> dict[str, Any] | None:
        nd = notice.get("ND") or notice.get("publication-number")
        titre = _pick_title(notice.get("TI"))
        if not nd or not titre:
            return None

        organisme = _pick_buyer(notice.get("buyer-name"))
        pd_raw = notice.get("PD") or ""
        date_publication = parse_date_flexible(pd_raw[:10])

        deadline_raw = notice.get("deadline-receipt-tender-date-lot")
        date_limite = None
        if isinstance(deadline_raw, str):
            date_limite = parse_date_flexible(deadline_raw[:10])
        elif isinstance(deadline_raw, list) and deadline_raw:
            date_limite = parse_date_flexible(str(deadline_raw[0])[:10])

        return {
            "titre": titre[:500],
            "organisme": organisme[:200],
            "description": titre[:2000],
            "date_publication": date_publication,
            "date_limite": date_limite,
            "lien_source": DETAIL_URL.format(nd=nd),
        }

    def run(self) -> dict[str, Any]:
        repo = ScraperRepository()
        source_id: Any = None
        nb_trouvees = 0
        nb_nouvelles = 0

        try:
            source_id = repo.get_source_id(SOURCE_NOM)
            logger.info("Démarrage scraper %s", SOURCE_NOM)

            today = datetime.now(timezone.utc).date()

            with httpx.Client(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                trust_env=False,
            ) as http:
                seen_nd: set[str] = set()

                for day_offset in range(LOOKBACK_DAYS):
                    day = today - timedelta(days=day_offset)
                    day_str = day.strftime("%Y%m%d")
                    query = f"PD>={day_str} AND PD<={day_str}"

                    next_token: str | None = None
                    for page in range(1, MAX_PAGES + 1):
                        body: dict[str, Any] = {
                            "query": query,
                            "limit": PAGE_SIZE,
                            "scope": "ACTIVE",
                            "fields": [
                                "ND",
                                "TI",
                                "PD",
                                "buyer-name",
                                "deadline-receipt-tender-date-lot",
                                "publication-number",
                            ],
                        }
                        if next_token:
                            body["iterationNextToken"] = next_token

                        response = http.post(API_URL, json=body)
                        response.raise_for_status()
                        payload = response.json()
                        notices = payload.get("notices") or []
                        if not notices:
                            break

                        for notice in notices:
                            nd = notice.get("ND") or notice.get("publication-number")
                            if not nd or nd in seen_nd:
                                continue
                            seen_nd.add(str(nd))

                            item = self._parse_notice(notice)
                            if not item:
                                continue
                            nb_trouvees += 1
                            hash_unique = compute_hash(
                                f"{item['lien_source']}|{item['titre']}",
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
                            "TED %s page %d : %d avis",
                            day.isoformat(),
                            page,
                            len(notices),
                        )

                        next_token = payload.get("iterationNextToken")
                        if not next_token:
                            break
                        time.sleep(0.3)

                    time.sleep(0.2)

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
