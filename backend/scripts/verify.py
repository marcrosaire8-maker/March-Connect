"""Script de vérification des données seedées dans MongoDB Atlas."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings


def verify() -> None:
    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        client.admin.command("ping")
        print("Connexion MongoDB Atlas : OK")
        print(f"Base de données : {settings.mongodb_db_name}")
        print()

        secteurs_count = db.secteurs.count_documents({})
        sources_count = db.sources.count_documents({})
        offres_count = db.offres.count_documents({})
        logs_count = db.logs_scraping.count_documents({})

        print(f"Collection secteurs       : {secteurs_count} document(s)")
        print(f"Collection sources        : {sources_count} document(s)")
        print(f"Collection offres         : {offres_count} document(s)")
        print(f"Collection logs_scraping  : {logs_count} document(s)")
        print()

        indexes_offres = db.offres.index_information()
        print("Index collection offres :")
        for name, info in indexes_offres.items():
            print(f"  - {name}: {info.get('key')}, unique={info.get('unique', False)}")
        print()

        expected_secteurs = 9
        expected_sources = 3

        if secteurs_count != expected_secteurs:
            raise SystemExit(
                f"ERREUR : {secteurs_count} secteurs trouvés, {expected_secteurs} attendus"
            )
        if sources_count != expected_sources:
            raise SystemExit(
                f"ERREUR : {sources_count} sources trouvées, {expected_sources} attendues"
            )

        hash_unique_index = next(
            (
                info
                for info in indexes_offres.values()
                if info.get("key") == [("hash_unique", 1)] and info.get("unique")
            ),
            None,
        )
        if not hash_unique_index:
            raise SystemExit("ERREUR : index unique sur hash_unique manquant")

        print("Vérification réussie : toutes les données seed sont présentes.")
    finally:
        client.close()


if __name__ == "__main__":
    verify()
