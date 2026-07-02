"""Scraper générique piloté par la fiche source MongoDB (sans scraper dédié)."""

from __future__ import annotations

import json
import logging
import random
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.models.enums import ScrapingStatus, ScrapingType
from app.scrapers.common import (
    USER_AGENT,
    ScraperRepository,
    build_error_result,
    build_success_result,
    compute_hash,
    infer_pays_from_text,
    normalize_pays_label,
    parse_date_flexible,
    parse_date_iso,
)
from app.scrapers.links import pick_most_specific_href, resolve_lien_source

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 45.0
DELAY_MIN = 0.8
DELAY_MAX = 1.8

TENDER_PATTERN = re.compile(
    r"appel|offre|march[ée]|tender|bid|procurement|concurrence|\bao\b|avis",
    re.IGNORECASE,
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/json,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
}


class GenericScraper:
    """Relève les offres pour toute source ajoutée en admin (hors scrapers dédiés)."""

    def __init__(self, source: dict[str, Any]) -> None:
        self.source = source
        self.source_id = source["_id"]
        self.nom = source["nom"]
        self.pays = source["pays"]
        self.url_base = source["url_base"].rstrip("/")
        raw_type = source.get("type_scraping", ScrapingType.HTML.value)
        self.type_scraping = (
            raw_type.value if isinstance(raw_type, ScrapingType) else str(raw_type)
        )
        self.config: dict[str, Any] = source.get("config") or {}
        self._repo = ScraperRepository()

    def _listing_url(self, page_index: int = 0) -> str:
        listing = self.config.get("listing_url") or self.url_base
        pagination = self.config.get("pagination") or {}
        start = int(pagination.get("start", 1))
        page_value = start + page_index
        if page_index <= 0 and start <= 1:
            return listing
        param = pagination.get("param", "page")
        separator = "&" if "?" in listing else "?"
        return f"{listing}{separator}{param}={page_value}"

    def _http_get(self, client: Any, url: str) -> Any:
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        headers = {**DEFAULT_HEADERS, "Referer": self.url_base}
        if self.config.get("http_client") == "curl_cffi":
            response = client.get(url, headers=headers, impersonate="chrome120")
        else:
            response = client.get(url, headers=headers)
        response.raise_for_status()
        return response

    def _absolute_url(self, href: str) -> str:
        if href.startswith("http"):
            return href
        return urljoin(f"{self.url_base}/", href.lstrip("/"))

    def _extract_field(
        self, element: Any, field_cfg: str | dict[str, Any]
    ) -> str:
        if isinstance(field_cfg, str):
            selector, attr = field_cfg, "text"
        else:
            selector = field_cfg["selector"]
            attr = field_cfg.get("attr", "text")

        if attr == "href" and isinstance(field_cfg, dict) and field_cfg.get("prefer_most_specific"):
            matches = element.select(selector)
            hrefs = [el.get("href", "") for el in matches if el.get("href")]
            listing = self.config.get("listing_url") or self.url_base
            return pick_most_specific_href(
                hrefs,
                url_base=self.url_base,
                listing_url=listing,
            )

        found = element.select_one(selector)
        if not found:
            return ""

        if attr == "text":
            return found.get_text(" ", strip=True)
        if attr == "href":
            return found.get("href", "") or ""
        if attr == "text_regex":
            text = found.get_text(" ", strip=True)
            pattern = field_cfg.get("pattern", "")
            if not pattern:
                return ""
            match = re.search(pattern, text)
            if not match:
                return ""
            group = int(field_cfg.get("group", 1))
            return match.group(group)
        return found.get(attr, "") or ""

    def _offre_pays(self, item: dict[str, Any]) -> str | None:
        if item.get("pays_extrait") and not item.get("pays"):
            return None
        if item.get("pays"):
            return item["pays"]
        if self.config.get("infer_pays_from_titre"):
            return infer_pays_from_text(item.get("titre", ""), self.pays)
        return self.pays

    def _parse_html_configured(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        item_selector = self.config["item_selector"]
        fields_cfg: dict[str, Any] = self.config.get("fields") or {}
        if "titre" not in fields_cfg:
            raise ValueError("config.fields.titre est requis pour le mode HTML configuré")

        offres: list[dict[str, Any]] = []
        for item in soup.select(item_selector):
            titre = self._extract_field(item, fields_cfg["titre"])
            if not titre:
                continue

            lien = ""
            if "lien_source" in fields_cfg:
                lien = self._extract_field(item, fields_cfg["lien_source"])
            listing = self.config.get("listing_url") or self.url_base
            if lien:
                lien = resolve_lien_source(
                    self._absolute_url(lien),
                    url_base=self.url_base,
                    listing_url=listing,
                ) or resolve_lien_source(
                    lien,
                    url_base=self.url_base,
                    listing_url=listing,
                )
            else:
                lien = ""

            organisme = (
                self._extract_field(item, fields_cfg["organisme"])
                if "organisme" in fields_cfg
                else self.nom
            )
            description = (
                self._extract_field(item, fields_cfg["description"])
                if "description" in fields_cfg
                else titre
            )
            date_pub_raw = (
                self._extract_field(item, fields_cfg["date_publication"])
                if "date_publication" in fields_cfg
                else ""
            )
            date_lim_raw = (
                self._extract_field(item, fields_cfg["date_limite"])
                if "date_limite" in fields_cfg
                else ""
            )
            pays_raw = (
                self._extract_field(item, fields_cfg["pays"])
                if "pays" in fields_cfg
                else ""
            )
            pays_label = normalize_pays_label(pays_raw) if pays_raw else None

            offres.append(
                {
                    "titre": titre,
                    "organisme": organisme or self.nom,
                    "description": description or titre,
                    "date_publication": parse_date_flexible(date_pub_raw),
                    "date_limite": parse_date_flexible(date_lim_raw),
                    "lien_source": lien,
                    "pays": pays_label,
                    "pays_extrait": bool(pays_raw.strip()),
                }
            )
        return offres

    def _parse_html_heuristic(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        seen_links: set[str] = set()
        offres: list[dict[str, Any]] = []

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:")):
                continue

            titre = anchor.get_text(" ", strip=True)
            if len(titre) < 8:
                continue

            full_link = self._absolute_url(href)
            if full_link in seen_links:
                continue

            combined = f"{titre} {href}"
            if not TENDER_PATTERN.search(combined):
                continue

            seen_links.add(full_link)
            parent = anchor.find_parent(["article", "tr", "li", "div"])
            context = parent.get_text(" ", strip=True) if parent else titre
            dates = re.findall(
                r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2}", context
            )
            date_publication = parse_date_flexible(dates[0]) if dates else None
            date_limite = parse_date_flexible(dates[1]) if len(dates) > 1 else None

            offres.append(
                {
                    "titre": titre[:500],
                    "organisme": self.nom,
                    "description": (context or titre)[:2000],
                    "date_publication": date_publication,
                    "date_limite": date_limite,
                    "lien_source": full_link,
                }
            )

        if not offres:
            raise ValueError(
                "Aucune offre détectée automatiquement. "
                "Ajoutez une config CSS (item_selector + fields) sur la source."
            )
        return offres

    def _parse_html(self, html: str) -> list[dict[str, Any]]:
        if self.config.get("item_selector"):
            return self._parse_html_configured(html)
        return self._parse_html_heuristic(html)

    def _parse_rss(self, content: str) -> list[dict[str, Any]]:
        root = ET.fromstring(content)
        items: list[Any] = []

        if root.tag.endswith("rss"):
            channel = root.find("channel")
            if channel is not None:
                items = channel.findall("item")
        elif root.tag.endswith("feed"):
            items = [
                el
                for el in root
                if el.tag.endswith("entry") or el.tag.endswith("item")
            ]

        offres: list[dict[str, Any]] = []
        for item in items:
            titre = self._xml_text(item, "title")
            lien = self._xml_text(item, "link")
            if not lien:
                link_el = item.find("{*}link")
                if link_el is not None:
                    lien = link_el.get("href", "")
            description = self._xml_text(item, "description") or self._xml_text(
                item, "summary"
            )
            pub = self._xml_text(item, "pubDate") or self._xml_text(item, "published")
            if not titre:
                continue
            offres.append(
                {
                    "titre": titre,
                    "organisme": self.nom,
                    "description": description or titre,
                    "date_publication": parse_date_flexible(pub),
                    "date_limite": None,
                    "lien_source": self._absolute_url(lien) if lien else self.url_base,
                }
            )
        return offres

    def _xml_text(self, parent: Any, tag: str) -> str:
        for child in parent:
            if child.tag.endswith(tag):
                return (child.text or "").strip()
        return ""

    def _items_from_json(self, data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if not isinstance(data, dict):
            return []

        for key in ("data", "results", "items", "content", "records", "tenders", "offres"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
            if isinstance(value, dict):
                for sub in ("items", "content", "results", "data"):
                    nested = value.get(sub)
                    if isinstance(nested, list):
                        return [x for x in nested if isinstance(x, dict)]
        return []

    def _pick(self, item: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = item.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    def _parse_api(self, data: Any) -> list[dict[str, Any]]:
        mapping = self.config.get("field_mapping") or {}
        items = self._items_from_json(data)
        if not items:
            raise ValueError("Réponse API : aucune liste d'offres détectée")

        offres: list[dict[str, Any]] = []
        for item in items:
            titre = self._pick(
                item,
                mapping.get("titre", "titre"),
                "titre",
                "title",
                "name",
                "libelle",
                "objet",
            )
            if not titre:
                continue

            lien = self._pick(
                item,
                mapping.get("lien_source", "lien_source"),
                "lien_source",
                "url",
                "link",
                "lien",
                "href",
            )
            organisme = self._pick(
                item,
                mapping.get("organisme", "organisme"),
                "organisme",
                "organization",
                "entite",
                "buyer",
            )
            description = self._pick(
                item,
                mapping.get("description", "description"),
                "description",
                "resume",
                "summary",
            )
            date_pub_raw = self._pick(
                item,
                mapping.get("date_publication", "date_publication"),
                "date_publication",
                "published_at",
                "datePublication",
                "created_at",
            )
            date_lim_raw = self._pick(
                item,
                mapping.get("date_limite", "date_limite"),
                "date_limite",
                "deadline",
                "dateLimite",
                "closing_date",
            )

            offres.append(
                {
                    "titre": titre,
                    "organisme": organisme or self.nom,
                    "description": description or titre,
                    "date_publication": parse_date_iso(date_pub_raw)
                    or parse_date_flexible(date_pub_raw),
                    "date_limite": parse_date_iso(date_lim_raw)
                    or parse_date_flexible(date_lim_raw),
                    "lien_source": self._absolute_url(lien) if lien else self.url_base,
                }
            )
        return offres

    def _fetch_offres(self, client: httpx.Client) -> list[dict[str, Any]]:
        pagination = self.config.get("pagination") or {}
        max_pages = int(pagination.get("max_pages", 1))
        all_offres: list[dict[str, Any]] = []

        for page in range(max_pages):
            url = self._listing_url(page)
            response = self._http_get(client, url)
            content_type = response.headers.get("content-type", "").lower()
            body = response.text

            if self.type_scraping == ScrapingType.RSS.value or body.lstrip().startswith(
                ("<?xml", "<rss", "<feed")
            ):
                page_offres = self._parse_rss(body)
            elif self.type_scraping == ScrapingType.API.value or "json" in content_type:
                page_offres = self._parse_api(response.json())
            else:
                page_offres = self._parse_html(body)

            logger.info("Page %d — %d offre(s) détectée(s)", page + 1, len(page_offres))
            all_offres.extend(page_offres)

            if page + 1 < max_pages and not page_offres:
                break

        return all_offres

    def _persist_offres(self, parsed: list[dict[str, Any]]) -> tuple[int, int]:
        nb_trouvees = len(parsed)
        nb_nouvelles = 0
        for item in parsed:
            pays = self._offre_pays(item)
            if not pays:
                continue
            hash_unique = compute_hash(
                item["titre"], item["organisme"], item["date_publication"]
            )
            offre = {
                "source_id": self.source_id,
                "secteur_id": None,
                "titre": item["titre"],
                "organisme": item["organisme"],
                "pays": pays,
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
        return nb_trouvees, nb_nouvelles

    def run(self) -> dict[str, Any]:
        nb_trouvees = 0
        nb_nouvelles = 0
        try:
            logger.info("Démarrage scraper générique — %s (%s)", self.nom, self.url_base)
            if self.config.get("http_client") == "curl_cffi":
                from curl_cffi import requests as curl_requests

                with curl_requests.Session(timeout=REQUEST_TIMEOUT) as client:
                    parsed = self._fetch_offres(client)
            else:
                with httpx.Client(
                    timeout=REQUEST_TIMEOUT,
                    follow_redirects=True,
                    trust_env=False,
                ) as client:
                    parsed = self._fetch_offres(client)

            nb_trouvees, nb_nouvelles = self._persist_offres(parsed)
            self._repo.update_source_execution(self.source_id)
            self._repo.log_execution(
                self.source_id, ScrapingStatus.SUCCES, nb_trouvees, nb_nouvelles
            )
            logger.info(
                "Scraping générique terminé : %d trouvée(s), %d nouvelle(s)",
                nb_trouvees,
                nb_nouvelles,
            )
            return build_success_result(nb_trouvees, nb_nouvelles)

        except httpx.TimeoutException as exc:
            msg = f"Timeout réseau après {REQUEST_TIMEOUT}s : {exc}"
            logger.error(msg)
            self._repo.log_execution(
                self.source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except httpx.HTTPError as exc:
            msg = f"Erreur HTTP : {exc}"
            logger.error(msg)
            self._repo.log_execution(
                self.source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except (ValueError, json.JSONDecodeError, ET.ParseError) as exc:
            msg = f"Données inattendues : {exc}"
            logger.error(msg)
            self._repo.log_execution(
                self.source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        except Exception as exc:
            msg = f"Erreur inattendue ({type(exc).__name__}) : {exc}"
            logger.error(msg, exc_info=True)
            self._repo.log_execution(
                self.source_id, ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )
            return build_error_result(
                ScrapingStatus.ECHEC, nb_trouvees, nb_nouvelles, msg
            )

        finally:
            self._repo.close()


def domain_from_url(url: str) -> str:
    host = urlparse(url).netloc or url
    return host.replace("www.", "")
