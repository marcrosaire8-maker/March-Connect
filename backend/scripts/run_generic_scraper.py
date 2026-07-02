#!/usr/bin/env python3
"""Lance le scraper générique pour les sources ajoutées en admin."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings
from app.models.enums import ScrapingType
from app.scrapers.generic_scraper import GenericScraper, domain_from_url
from app.scrapers.registry import SCRAPER_REGISTRY

logger = logging.getLogger(__name__)


def get_db():
    client = MongoClient(settings.mongodb_uri)
    return client, client[settings.mongodb_db_name]


def list_generic_sources(db) -> list[dict]:
    sources = list(db.sources.find({"actif": True}).sort("nom", 1))
    return [s for s in sources if s["nom"] not in SCRAPER_REGISTRY]


def run_source(source: dict) -> dict:
    result = GenericScraper(source).run()
    return {"source": source["nom"], **result}


def create_source(
    db,
    *,
    nom: str,
    pays: str,
    url: str,
    type_scraping: str,
    config: dict | None = None,
) -> dict:
    doc = {
        "nom": nom,
        "pays": pays,
        "url_base": url.rstrip("/"),
        "type_scraping": type_scraping,
        "actif": True,
        "derniere_execution": None,
    }
    if config:
        doc["config"] = config

    existing = db.sources.find_one({"nom": nom})
    if existing:
        db.sources.update_one({"_id": existing["_id"]}, {"$set": doc})
        doc["_id"] = existing["_id"]
        logger.info("Source mise à jour : %s", nom)
    else:
        inserted = db.sources.insert_one(doc)
        doc["_id"] = inserted.inserted_id
        logger.info("Source créée : %s", nom)
    return doc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scraper générique pour les sources admin (hors scrapers dédiés)"
    )
    parser.add_argument("--source-id", help="ID MongoDB de la source à scraper")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scraper toutes les sources actives sans scraper dédié",
    )
    parser.add_argument("--nom", help="Nom de la source (avec --url pour créer + scraper)")
    parser.add_argument("--pays", help="Pays de la source")
    parser.add_argument("--url", help="URL de la page ou de l'API")
    parser.add_argument(
        "--type",
        choices=[t.value for t in ScrapingType],
        default=ScrapingType.HTML.value,
        help="Type de scraping (défaut: html)",
    )
    parser.add_argument(
        "--config",
        help="Config JSON optionnelle (selecteurs CSS, pagination, mapping API)",
    )
    parser.add_argument(
        "--create-only",
        action="store_true",
        help="Créer/mettre à jour la source sans lancer le scraping",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    config = json.loads(args.config) if args.config else None
    client, db = get_db()

    try:
        if args.nom and args.url:
            if not args.pays:
                print("Erreur : --pays est requis avec --nom et --url", file=sys.stderr)
                return 1
            source = create_source(
                db,
                nom=args.nom,
                pays=args.pays,
                url=args.url,
                type_scraping=args.type,
                config=config,
            )
            if args.create_only:
                print(f"Source enregistrée : {source['nom']} ({source['_id']})")
                return 0
            result = run_source(source)
            _print_result(result)
            return 0 if result["statut"] == "succes" else 1

        if args.source_id:
            if not ObjectId.is_valid(args.source_id):
                print("Erreur : source-id invalide", file=sys.stderr)
                return 1
            source = db.sources.find_one({"_id": ObjectId(args.source_id)})
            if not source:
                print("Erreur : source introuvable", file=sys.stderr)
                return 1
            if source["nom"] in SCRAPER_REGISTRY:
                print(
                    f"Info : « {source['nom']} » utilise un scraper dédié. "
                    "Utilisez POST /api/scraping/trigger ou le module dédié.",
                    file=sys.stderr,
                )
                return 1
            result = run_source(source)
            _print_result(result)
            return 0 if result["statut"] == "succes" else 1

        if args.all:
            sources = list_generic_sources(db)
            if not sources:
                print("Aucune source générique active à traiter.")
                return 0
            exit_code = 0
            for source in sources:
                result = run_source(source)
                _print_result(result)
                if result["statut"] != "succes":
                    exit_code = 1
            return exit_code

        # Mode rapide : URL seule → nom auto depuis le domaine
        if args.url and not args.nom:
            auto_nom = domain_from_url(args.url)
            auto_pays = args.pays or "—"
            source = create_source(
                db,
                nom=auto_nom,
                pays=auto_pays,
                url=args.url,
                type_scraping=args.type,
                config=config,
            )
            result = run_source(source)
            _print_result(result)
            return 0 if result["statut"] == "succes" else 1

        parser.print_help()
        return 1
    finally:
        client.close()


def _print_result(result: dict) -> None:
    print(
        f"\nSource          : {result.get('source', '—')}\n"
        f"Statut          : {result['statut']}\n"
        f"Offres trouvées : {result['nb_offres_trouvees']}\n"
        f"Nouvelles offres: {result['nb_offres_nouvelles']}"
    )
    if result.get("message_erreur"):
        print(f"Erreur          : {result['message_erreur']}")


if __name__ == "__main__":
    sys.exit(main())
