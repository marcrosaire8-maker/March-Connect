"""Script de seed initial pour les secteurs et sources."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings
from app.db.sector_seed import SECTEUR_SEED_DATA
from app.scrapers.sources_config import SCRAPER_SOURCES

SECTEURS = SECTEUR_SEED_DATA

SOURCES = [
    {**source, "derniere_execution": None} for source in SCRAPER_SOURCES
]


def ensure_indexes(db) -> None:
    db.offres.create_index(
        [("hash_unique", ASCENDING)], unique=True, name="hash_unique"
    )
    db.offres.create_index([("secteur_id", ASCENDING)])
    db.offres.create_index([("pays", ASCENDING)])
    db.offres.create_index([("source_id", ASCENDING)])
    db.logs_scraping.create_index([("source_id", ASCENDING)])
    db.logs_scraping.create_index([("date_execution", ASCENDING)])
    db.sources.create_index([("pays", ASCENDING)])
    db.secteurs.create_index([("nom", ASCENDING)], unique=True)


def seed() -> None:
    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        client.admin.command("ping")
        print("Connexion MongoDB Atlas : OK")

        ensure_indexes(db)
        print("Index créés ou déjà présents")

        secteurs_result = db.secteurs.delete_many({})
        sources_result = db.sources.delete_many({})
        print(
            f"Nettoyage pré-seed : {secteurs_result.deleted_count} secteur(s), "
            f"{sources_result.deleted_count} source(s) supprimé(s)"
        )

        secteurs_insert = db.secteurs.insert_many(SECTEURS)
        sources_insert = db.sources.insert_many(SOURCES)

        print(f"Secteurs insérés : {len(secteurs_insert.inserted_ids)}")
        print(f"Sources insérées : {len(sources_insert.inserted_ids)}")

        for secteur in db.secteurs.find().sort("nom", 1):
            print(f"  - Secteur : {secteur['nom']} ({len(secteur['mots_cles'])} mots-clés)")

        for source in db.sources.find().sort("nom", 1):
            print(f"  - Source : {source['nom']} ({source['pays']})")

        print("Seed terminé avec succès.")
    finally:
        client.close()


if __name__ == "__main__":
    seed()
