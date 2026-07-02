"""Métadonnées des sources avec scraper dédié (seed + bootstrap)."""

from __future__ import annotations

from app.models.enums import ScrapingType

SCRAPER_SOURCES: list[dict] = [
    {
        "nom": "Portail Marchés Publics Bénin",
        "pays": "Bénin",
        "url_base": "https://www.marches-publics.bj",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
    },
    {
        "nom": "SBEE Bénin",
        "pays": "Bénin",
        "url_base": "https://marches-publics.sbee.bj",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
    },
    {
        "nom": "SRTB Direct Bénin TV",
        "pays": "Bénin",
        "url_base": "https://srtb.bj/directbenintv",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
        "config": {
            "listing_url": "https://srtb.bj/directbenintv/",
            "item_selector": "article.hentry.penci-post-item",
            "fields": {
                "titre": {"selector": ".entry-title a", "attr": "text"},
                "lien_source": {"selector": ".entry-title a", "attr": "href"},
                "date_publication": {"selector": "time.entry-date", "attr": "datetime"},
            },
        },
    },
    {
        "nom": "BOAD Appels d'offres",
        "pays": "Togo",
        "url_base": "https://www.boad.org",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
        "config": {
            "listing_url": "https://www.boad.org/fr/opportunites/appels-doffre/",
            "item_selector": "div.bg-boad-gray",
            "infer_pays_from_titre": True,
            "fields": {
                "titre": {"selector": "h2.text-2xl", "attr": "text"},
                "lien_source": {
                    "selector": "a[href*='/fr/opportunites/appels-doffre/']",
                    "attr": "href",
                    "prefer_most_specific": True,
                },
                "date_limite": {
                    "selector": "div.space-y-5",
                    "attr": "text_regex",
                    "pattern": r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
                    "group": 2,
                },
            },
        },
    },
    {
        "nom": "Banque Africaine de Développement",
        "pays": "Côte d'Ivoire",
        "url_base": "https://www.afdb.org",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
        "config": {
            "http_client": "curl_cffi",
            "listing_url": "https://www.afdb.org/fr/documents/project-related-procurement/specific-procurement-notices",
            "item_selector": ".view-content .row > div",
            "infer_pays_from_titre": True,
            "pagination": {"param": "page", "start": 0, "max_pages": 3},
            "fields": {
                "titre": {"selector": ".views-field-title a", "attr": "text"},
                "lien_source": {"selector": ".views-field-title a", "attr": "href"},
                "date_publication": {
                    "selector": ".views-field-field-publication-date .date-display-single",
                    "attr": "content",
                },
            },
        },
    },
    {
        "nom": "Banque Islamique de Développement",
        "pays": "Bénin",
        "url_base": "https://www.isdb.org",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
        "config": {
            "listing_url": "https://www.isdb.org/project-procurement/tenders",
            "item_selector": ".views-row article.type-tender",
            "fields": {
                "titre": {"selector": "h2 a", "attr": "text"},
                "lien_source": {"selector": "h2 a", "attr": "href"},
                "date_limite": {
                    "selector": ".field--name-field-close-date time",
                    "attr": "text",
                },
                "pays": {
                    "selector": ".field--name-field-world-country",
                    "attr": "text",
                },
            },
        },
    },
    {
        "nom": "Portail Marchés Publics Sénégal",
        "pays": "Sénégal",
        "url_base": "https://www.achatspublics.sn",
        "type_scraping": ScrapingType.API.value,
        "actif": True,
    },
    {
        "nom": "Marchés du Sénégal",
        "pays": "Sénégal",
        "url_base": "https://marchesdusenegal.com",
        "type_scraping": ScrapingType.HTML.value,
        "actif": False,
    },
    {
        "nom": "DGMP Côte d'Ivoire",
        "pays": "Côte d'Ivoire",
        "url_base": "https://marchespublics.ci",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
    },
    {
        "nom": "DGMP Mali",
        "pays": "Mali",
        "url_base": "https://dgmp.gouv.ml",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
    },
    {
        "nom": "Marchés Publics Togo",
        "pays": "Togo",
        "url_base": "https://marchespublicstogo.com",
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
    },
    {
        "nom": "BOAMP France",
        "pays": "France",
        "url_base": "https://www.boamp.fr",
        "type_scraping": ScrapingType.API.value,
        "actif": True,
    },
    {
        "nom": "TED Europe",
        "pays": "Europe",
        "url_base": "https://ted.europa.eu",
        "type_scraping": ScrapingType.API.value,
        "actif": True,
    },
    {
        "nom": "eTenders Afrique du Sud",
        "pays": "Afrique du Sud",
        "url_base": "https://www.etenders.gov.za",
        "type_scraping": ScrapingType.API.value,
        "actif": True,
    },
]
