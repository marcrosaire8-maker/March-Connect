"""Probe marches-publics.bj listing API and write api_probe_notes.txt."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import httpx

USER_AGENT = "MarchesPublicsOuest-Bot/0.1"
BASE_URL = "https://www.marches-publics.bj"
API_BASE = "https://api.marches-publics.bj/v2"
LISTING_PAGE = f"{BASE_URL}/appels-doffres"
HTML_PATH = Path("/tmp/mpbj.html")
NOTES_PATH = Path(__file__).resolve().parent / "api_probe_notes.txt"
TIMEOUT = 45.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Origin": BASE_URL,
    "Referer": LISTING_PAGE,
}

GREP_TERMS = [
    "api.marches-publics.bj",
    "appels-doffres",
    "announcements",
    "x-api",
    "authorization",
    "bearer",
    "token",
    "/v2/",
]

ENDPOINT_CANDIDATES = [
    "/appels-doffres",
    "/appels-doffres/search",
    "/portal/appels-doffres",
    "/public/appels-doffres",
    "/open/appels-doffres",
    "/announcements",
    "/announcements/search",
    "/avis-appel-concurrence",
    "/marches",
    "/marches/search",
]

PARAM_SETS = [
    {},
    {"page": 0, "size": 20},
    {"page": 1, "size": 20},
    {"page": 0, "limit": 20},
    {"page": 1, "limit": 20},
    {"status": 0},
    {"status": 1},
    {"status": 2},
    {"status": "0"},
    {"status": "1"},
    {"status": "2"},
]


def log(lines: list[str], msg: str = "") -> None:
    if msg:
        lines.append(msg)
        print(msg)


def resolve_script_url(src: str) -> str:
    if src.startswith("http"):
        return src
    if src.startswith("//"):
        return "https:" + src
    return f"{BASE_URL}/{src.lstrip('/')}"


def grep_js_context(js: str, term: str, window: int = 100) -> list[str]:
    out: list[str] = []
    low = js.lower()
    t = term.lower()
    start = 0
    while True:
        idx = low.find(t, start)
        if idx < 0:
            break
        out.append(js[max(0, idx - window) : idx + window])
        start = idx + len(t)
        if len(out) >= 8:
            break
    return out


def extract_api_paths_from_js(js: str) -> set[str]:
    patterns = [
        r"https://api\.marches-publics\.bj/v2/[a-zA-Z0-9_./-]+",
        r'["\'](/v2/[a-zA-Z0-9_./-]+)["\']',
        r"appels-doffres[a-zA-Z0-9_./-]*",
    ]
    found: set[str] = set()
    for pat in patterns:
        for m in re.findall(pat, js):
            found.add(m if isinstance(m, str) else m[0])
    return found


def find_embedded_json(html: str) -> list[str]:
    hints: list[str] = []
    if "__NEXT_DATA__" in html:
        hints.append("__NEXT_DATA__ present")
    if "application/ld+json" in html:
        hints.append("application/ld+json script(s)")
    for pat in [
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
        r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});",
    ]:
        for m in re.findall(pat, html, re.S | re.I):
            snippet = m[:500] if isinstance(m, str) else str(m)[:500]
            hints.append(f"embedded JSON snippet: {snippet[:200]}...")
    return hints


def detect_ssr_cards(html: str) -> dict[str, Any]:
    lower = html.lower()
    keywords = [
        "appel",
        "offre",
        "avis",
        "date limite",
        "publication",
        "organisme",
    ]
    hits = {k: lower.count(k) for k in keywords}
    has_ng = "ng-" in html or "_ngcontent" in html
    has_react = "__NEXT_DATA__" in html or "react" in lower
    return {
        "keyword_counts": hits,
        "likely_spa_shell": has_ng or has_react or len(html) < 50_000,
        "has_tender_like_markup": any(
            x in lower
            for x in ["card", "tender", "marche", "ao-", "appel-d-offre", "listing"]
        ),
    }


def try_parse_json(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def summarize_item_fields(obj: Any) -> dict[str, str | None]:
    """Map common API keys to scraper fields (best effort)."""
    if not isinstance(obj, dict):
        return {}
    key_map = {
        "titre": ["titre", "title", "objet", "label", "name", "libelle"],
        "organisme": [
            "organisme",
            "organization",
            "authority",
            "maitreOuvrage",
            "maitre_ouvrage",
            "entity",
            "structure",
        ],
        "date_publication": [
            "datePublication",
            "date_publication",
            "publishedAt",
            "publicationDate",
            "datePub",
        ],
        "date_limite": [
            "dateLimite",
            "date_limite",
            "deadline",
            "closingDate",
            "dateCloture",
            "dateFin",
        ],
        "lien": ["lien", "url", "link", "href", "slug", "id", "reference"],
    }
    result: dict[str, str | None] = {}
    lower_keys = {k.lower(): k for k in obj.keys() if isinstance(k, str)}
    for field, candidates in key_map.items():
        result[field] = None
        for c in candidates:
            if c in obj:
                result[field] = c
                break
            if c.lower() in lower_keys:
                result[field] = lower_keys[c.lower()]
                break
    return result


def main() -> int:
    lines: list[str] = []
    findings: dict[str, Any] = {
        "api_base": API_BASE,
        "listing_endpoints": [],
        "required_headers": [],
        "query_params": {},
        "field_mapping": {},
        "sample_snippet": None,
        "tender_count_assessment": "UNKNOWN",
        "html_ssr": {},
        "script_srcs": [],
        "errors": [],
    }

    log(lines, f"Probe started — listing page: {LISTING_PAGE}")

    try:
        with httpx.Client(
            timeout=TIMEOUT,
            follow_redirects=True,
            headers=DEFAULT_HEADERS,
            trust_env=False,
        ) as client:
            resp = client.get(LISTING_PAGE)
            html = resp.text
            HTML_PATH.write_text(html, encoding="utf-8")
            log(lines, f"HTML saved: {HTML_PATH} ({len(html)} bytes, HTTP {resp.status_code})")

            scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I)
            findings["script_srcs"] = scripts
            log(lines, f"Script src URLs ({len(scripts)}):")
            for s in scripts:
                log(lines, f"  - {s}")

            embedded = find_embedded_json(html)
            ssr = detect_ssr_cards(html)
            findings["html_ssr"] = {"embedded": embedded, "analysis": ssr}
            log(lines, f"Embedded JSON hints: {embedded or 'none'}")
            log(lines, f"SSR/card analysis: {json.dumps(ssr, ensure_ascii=False)}")

            extra_headers: dict[str, str] = {}
            js_paths: set[str] = set()
            for src in scripts[:12]:
                url = resolve_script_url(src)
                try:
                    js = client.get(url).text
                except Exception as exc:
                    log(lines, f"JS fetch failed {url}: {exc}")
                    continue
                log(lines, f"JS bundle {url} ({len(js)} chars)")
                for term in GREP_TERMS:
                    if term.lower() in js.lower():
                        for ctx in grep_js_context(js, term)[:2]:
                            log(lines, f"  grep [{term}]: ...{ctx[:180]}...")
                js_paths |= extract_api_paths_from_js(js)
                for hdr in re.findall(
                    r'["\'](x-api[a-z-]*|authorization|api[_-]?key)["\']\s*:\s*["\']([^"\']+)["\']',
                    js,
                    re.I,
                ):
                    extra_headers[hdr[0]] = hdr[1]
                for hdr_name in re.findall(
                    r'headers\s*:\s*\{([^}]{0,400})\}', js, re.I
                ):
                    if "api" in hdr_name.lower() or "auth" in hdr_name.lower():
                        log(lines, f"  headers block: {hdr_name[:300]}")

            if js_paths:
                log(lines, "API path strings from JS:")
                for p in sorted(js_paths)[:40]:
                    log(lines, f"  - {p}")

            api_headers = dict(DEFAULT_HEADERS)
            api_headers.update(extra_headers)
            if extra_headers:
                findings["required_headers"] = list(extra_headers.keys())
                log(lines, f"Extra headers from JS: {extra_headers}")

            endpoints = list(ENDPOINT_CANDIDATES)
            for p in sorted(js_paths):
                if p.startswith("http"):
                    endpoints.append(p.replace(API_BASE, ""))
                elif p.startswith("/v2/"):
                    endpoints.append(p.replace("/v2", ""))
                elif p.startswith("/"):
                    endpoints.append(p)

            seen_eps: set[str] = set()
            unique_eps = []
            for ep in endpoints:
                if ep not in seen_eps:
                    seen_eps.add(ep)
                    unique_eps.append(ep)

            log(lines, "\n=== API GET probes ===")
            best: tuple[str, dict, httpx.Response] | None = None
            for endpoint in unique_eps:
                if not endpoint.startswith("/"):
                    endpoint = "/" + endpoint
                for params in PARAM_SETS:
                    url = f"{API_BASE}{endpoint}"
                    try:
                        r = client.get(url, params=params, headers=api_headers)
                    except Exception as exc:
                        findings["errors"].append(f"{url} {params}: {exc}")
                        continue
                    if r.status_code == 200 and "json" in r.headers.get(
                        "content-type", ""
                    ).lower():
                        data = try_parse_json(r.text)
                        if data is not None:
                            log(
                                lines,
                                f"OK 200 {url} params={params} body_len={len(r.text)}",
                            )
                            if best is None:
                                best = (url, params, r)
                    elif r.status_code not in (404, 401, 403):
                        log(
                            lines,
                            f"{r.status_code} {url} params={params} -> {r.text[:120]!r}",
                        )

            log(lines, "\n=== FINDINGS SUMMARY ===")
            if best:
                url, params, r = best
                findings["listing_endpoints"] = [url.replace(API_BASE, "")]
                findings["query_params"] = params
                data = json.loads(r.text)
                findings["sample_snippet"] = r.text[:2500]
                items: list[Any] = []
                if isinstance(data, dict):
                    for k in (
                        "content",
                        "data",
                        "items",
                        "results",
                        "appelsDoffres",
                        "announcements",
                    ):
                        if isinstance(data.get(k), list):
                            items = data[k]
                            findings["tender_count_assessment"] = (
                                f"{len(items)} items in '{k}' (page); "
                                f"total={data.get('totalElements') or data.get('total') or '?'}"
                            )
                            break
                    if not items and isinstance(data.get("page"), dict):
                        pg = data["page"]
                        if isinstance(pg.get("content"), list):
                            items = pg["content"]
                if items and isinstance(items[0], dict):
                    findings["field_mapping"] = summarize_item_fields(items[0])
                log(lines, f"API base URL: {API_BASE}")
                log(lines, f"Listing endpoint path: {findings['listing_endpoints']}")
                log(lines, f"Working query params: {params}")
                log(lines, f"Required/extra headers: {findings['required_headers'] or 'none beyond browser-like defaults'}")
                log(lines, f"Field mapping (API key -> logical): {findings['field_mapping']}")
                log(lines, f"Tender count: {findings['tender_count_assessment']}")
                log(lines, f"Sample JSON:\n{r.text[:2000]}")
            else:
                findings["tender_count_assessment"] = (
                    "No JSON 200 response from probed endpoints; check HTML SSR or missing auth/params"
                )
                log(lines, "No successful JSON listing response in probe matrix.")
                log(lines, f"API base URL (from JS/domain): {API_BASE}")
                log(lines, "Listing endpoint path(s): NOT CONFIRMED")
                log(lines, "Required headers: NOT CONFIRMED")
                log(lines, "Query params: NOT CONFIRMED (tried status 0/1/2, page, limit, size)")
                log(lines, f"Tender count: {findings['tender_count_assessment']}")

    except Exception as exc:
        err = f"PROBE_ABORTED: {type(exc).__name__}: {exc}"
        findings["errors"].append(err)
        log(lines, err)

    summary_block = [
        "",
        "=" * 60,
        "STRUCTURED FINDINGS (for scraper)",
        "=" * 60,
        json.dumps(findings, indent=2, ensure_ascii=False),
    ]
    lines.extend(summary_block)
    NOTES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(lines, f"\nNotes written to {NOTES_PATH}")
    return 0 if findings.get("listing_endpoints") else 1


if __name__ == "__main__":
    sys.exit(main())
