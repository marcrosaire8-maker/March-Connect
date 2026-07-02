#!/usr/bin/env python3
"""Crée ou promeut un compte administrateur."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

from app.core.security import hash_password
from app.db.config import settings
from app.models.enums import UserRole


def main() -> int:
    parser = argparse.ArgumentParser(description="Créer ou promouvoir un admin")
    parser.add_argument("--email", default=settings.admin_email, help="Email admin")
    parser.add_argument(
        "--password",
        default=settings.admin_password,
        help="Mot de passe (min. 8 caractères)",
    )
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Promouvoir un compte existant au lieu d'échouer",
    )
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Réinitialiser le mot de passe d'un compte existant",
    )
    args = parser.parse_args()

    if not args.email or not args.password:
        print(
            "Erreur : définissez ADMIN_EMAIL et ADMIN_PASSWORD dans .env\n"
            "ou passez --email et --password",
            file=sys.stderr,
        )
        return 1

    if len(args.password) < 8:
        print("Erreur : le mot de passe doit faire au moins 8 caractères", file=sys.stderr)
        return 1

    email = args.email.lower()
    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    existing = db.utilisateurs.find_one({"email": email})
    if existing:
        if args.reset_password:
            db.utilisateurs.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "mot_de_passe_hash": hash_password(args.password),
                        "must_change_password": False,
                        "role": UserRole.ADMIN.value,
                    }
                },
            )
            print(f"Mot de passe réinitialisé pour : {email}")
            return 0
        if existing.get("role") == UserRole.ADMIN.value:
            print(f"Admin déjà existant : {email}")
            return 0
        if args.promote:
            db.utilisateurs.update_one(
                {"_id": existing["_id"]},
                {"$set": {"role": UserRole.ADMIN.value}},
            )
            print(f"Compte promu administrateur : {email}")
            return 0
        print(
            f"Un compte client existe déjà pour {email}. "
            "Relancez avec --promote pour le promouvoir admin.",
            file=sys.stderr,
        )
        return 1

    db.utilisateurs.insert_one(
        {
            "email": email,
            "mot_de_passe_hash": hash_password(args.password),
            "role": UserRole.ADMIN.value,
            "date_inscription": datetime.now(timezone.utc),
        }
    )
    print(f"Administrateur créé : {email}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
