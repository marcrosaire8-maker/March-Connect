"""Registre central des scrapers par nom de source."""

from __future__ import annotations

import logging
from typing import Any

from pymongo import MongoClient

from app.db.config import settings
from app.scrapers.generic_scraper import GenericScraper
from app.scrapers.boamp_fr import BoampFrScraper
from app.scrapers.dgmp_mali import DgmpMaliScraper
from app.scrapers.etenders_za import EtendersZaScraper
from app.scrapers.marchespublics_ci import MarchesPublicsCiScraper
from app.scrapers.marches_publics_bj import MarchesPublicsBjScraper
from app.scrapers.marches_senegal import MarchesSenegalScraper
from app.scrapers.marches_togo import MarchesTogoScraper
from app.scrapers.sbee_bj import SbeeBjScraper
from app.scrapers.ted_europa import TedEuropaScraper

logger = logging.getLogger(__name__)

SCRAPER_REGISTRY: dict[str, type] = {
    "Portail Marchés Publics Bénin": MarchesPublicsBjScraper,
    "SBEE Bénin": SbeeBjScraper,
    "Portail Marchés Publics Sénégal": MarchesSenegalScraper,
    "DGMP Côte d'Ivoire": MarchesPublicsCiScraper,
    "DGMP Mali": DgmpMaliScraper,
    "Marchés Publics Togo": MarchesTogoScraper,
    "BOAMP France": BoampFrScraper,
    "TED Europe": TedEuropaScraper,
    "eTenders Afrique du Sud": EtendersZaScraper,
}


def is_dedicated_source(source_nom: str) -> bool:
    return source_nom in SCRAPER_REGISTRY


def run_scraper_for_source(source: dict[str, Any]) -> dict[str, Any]:
    """Lance le scraper dédié ou le scraper générique selon la source."""
    nom = source["nom"]
    if is_dedicated_source(nom):
        return SCRAPER_REGISTRY[nom]().run()
    return GenericScraper(source).run()


def run_all_scrapers() -> list[dict]:
    """Lance les scrapers dédiés actifs puis les sources génériques actives en base."""
    results: list[dict] = []

    client = MongoClient(settings.mongodb_uri)
    try:
        db = client[settings.mongodb_db_name]
        active_names = {
            s["nom"]
            for s in db.sources.find({"actif": True, "utilisateur_id": {"$exists": False}})
        }

        for source_nom, scraper_cls in SCRAPER_REGISTRY.items():
            if source_nom not in active_names:
                logger.info("Scheduler — scraper %s ignoré (inactif)", source_nom)
                continue
            logger.info("Scheduler — lancement scraper dédié %s", source_nom)
            try:
                results.append({"source": source_nom, **scraper_cls().run()})
            except Exception as exc:
                logger.error("Scraper %s échoué : %s", source_nom, exc, exc_info=True)
                results.append(
                    {
                        "source": source_nom,
                        "statut": "echec",
                        "nb_offres_trouvees": 0,
                        "nb_offres_nouvelles": 0,
                        "message_erreur": str(exc),
                    }
                )

        for source in db.sources.find({"actif": True}).sort("nom", 1):
            if is_dedicated_source(source["nom"]):
                continue
            logger.info("Scheduler — lancement scraper générique %s", source["nom"])
            try:
                results.append({"source": source["nom"], **GenericScraper(source).run()})
            except Exception as exc:
                logger.error("Scraper %s échoué : %s", source["nom"], exc, exc_info=True)
                results.append(
                    {
                        "source": source["nom"],
                        "statut": "echec",
                        "nb_offres_trouvees": 0,
                        "nb_offres_nouvelles": 0,
                        "message_erreur": str(exc),
                    }
                )
    finally:
        client.close()

    return results
