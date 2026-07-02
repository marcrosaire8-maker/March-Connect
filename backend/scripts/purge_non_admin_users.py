#!/usr/bin/env python3
"""Supprime tous les comptes sauf l'administrateur et leurs données associées."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings
from app.db.connection import close_client, get_database
from app.models.enums import UserRole
from app.services.user_cleanup import delete_user_and_data


async def main() -> int:
    db = get_database()
    admin_email = (settings.admin_email or "").lower()

    users = await db.utilisateurs.find({}).to_list(length=10_000)
    to_delete = [
        u
        for u in users
        if u.get("role") != UserRole.ADMIN.value
        and u.get("email", "").lower() != admin_email
    ]

    print(f"Comptes trouvés : {len(users)} — à supprimer : {len(to_delete)}")

    deleted = 0
    for user in to_delete:
        ok = await delete_user_and_data(db, user["_id"], user["email"])
        if ok:
            deleted += 1
            print(f"  supprimé : {user['email']}")

    # abonnés orphelins sans utilisateur
    orphan_abonnes = await db.abonnes.find(
        {
            "$or": [
                {"utilisateur_id": {"$exists": False}},
                {"utilisateur_id": None},
            ]
        }
    ).to_list(length=10_000)
    for ab in orphan_abonnes:
        if ab.get("email", "").lower() == admin_email:
            continue
        await db.notifications_envoyees.delete_many({"abonne_id": ab["_id"]})
        await db.abonnes.delete_one({"_id": ab["_id"]})
        print(f"  abonné orphelin supprimé : {ab.get('email')}")

    remaining = await db.utilisateurs.count_documents({})
    print(f"Terminé — {deleted} compte(s) supprimé(s), {remaining} compte(s) restant(s).")
    await close_client()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
