#!/usr/bin/env python3
"""Vérifie manuellement l'email d'un utilisateur (prod / dépannage)."""

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

from app.db.config import settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Marquer un email comme vérifié")
    parser.add_argument("email", help="Adresse email à activer")
    args = parser.parse_args()

    email = args.email.strip().lower()
    client = MongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    user = db.utilisateurs.find_one({"email": email})
    if not user:
        print(f"Aucun compte pour {email}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    db.utilisateurs.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "email_verifie": True,
                "statut_email": "verifie",
                "date_verification_email": now,
            }
        },
    )
    db.email_verification_otps.delete_one({"email": email})
    print(f"Email vérifié manuellement : {email}")
    print("L'utilisateur peut maintenant se connecter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
