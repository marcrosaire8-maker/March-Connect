"""Validation et sélection des liens sources vers une fiche d'offre précise."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

LISTING_PATHS = frozenset(
    {
        "",
        "/",
        "/appel_offre",
        "/appels-doffres",
        "/consultations",
        "/fr/opportunites/appels-doffre",
        "/project-procurement/tenders",
        "/fr/documents/project-related-procurement/specific-procurement-notices",
    }
)


def _path_segments(url: str) -> list[str]:
    return [segment for segment in urlparse(url).path.split("/") if segment]


def is_specific_lien_source(
    lien: str,
    *,
    url_base: str = "",
    listing_url: str = "",
) -> bool:
    if not lien or not lien.strip():
        return False

    path = urlparse(lien.strip()).path.rstrip("/") or "/"
    if path in LISTING_PATHS:
        return False

    listing_path = urlparse(listing_url).path.rstrip("/") if listing_url else ""
    base_path = urlparse(url_base).path.rstrip("/") if url_base else ""

    if listing_path and path == listing_path:
        return False
    if base_path and path == base_path:
        return False

    if re.search(r"/\d{3,}(?:/|$)", path):
        return True

    listing_depth = len(_path_segments(listing_url)) if listing_url else 0
    if listing_depth and len(_path_segments(lien)) > listing_depth:
        return True

    return len(_path_segments(lien)) >= 3


def pick_most_specific_href(
    candidates: list[str],
    *,
    url_base: str = "",
    listing_url: str = "",
) -> str:
    cleaned = [href.strip() for href in candidates if href and href.strip()]
    if not cleaned:
        return ""

    specific = [
        href
        for href in cleaned
        if is_specific_lien_source(href, url_base=url_base, listing_url=listing_url)
    ]
    pool = specific or cleaned
    return max(pool, key=lambda href: (len(_path_segments(href)), len(href)))


def resolve_lien_source(
    href: str,
    *,
    url_base: str,
    listing_url: str = "",
) -> str:
    if not href:
        return ""
    absolute = href if href.startswith("http") else urljoin(f"{url_base.rstrip('/')}/", href.lstrip("/"))
    if is_specific_lien_source(absolute, url_base=url_base, listing_url=listing_url):
        return absolute
    return ""


def lien_is_better(candidate: str, current: str | None, *, url_base: str = "", listing_url: str = "") -> bool:
    if not candidate:
        return False
    if not current:
        return is_specific_lien_source(candidate, url_base=url_base, listing_url=listing_url)
    if not is_specific_lien_source(current, url_base=url_base, listing_url=listing_url):
        return is_specific_lien_source(candidate, url_base=url_base, listing_url=listing_url)
    return len(_path_segments(candidate)) > len(_path_segments(current))
