#!/usr/bin/env python3
"""Supprime tous les comptes sauf l'administrateur et leurs données associées.

Sécurité :
  --dry-run          Affiche ce qui serait supprimé sans rien modifier
  --backup-dir DIR   Exporte un JSON de sauvegarde avant suppression (défaut: backups/)
  --yes              Saute la confirmation interactive (dangereux)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings
from app.db.connection import close_client, get_database
from app.models.enums import UserRole
from app.services.user_cleanup import delete_user_and_data

CONFIRMATION_TOKEN = "SUPPRIMER"


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    return {key: _json_default(val) if key == "_id" or isinstance(val, datetime) else val for key, val in doc.items()}


async def _collect_targets(db, admin_email: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    users = await db.utilisateurs.find({}).to_list(length=10_000)
    to_delete = [
        u
        for u in users
        if u.get("role") != UserRole.ADMIN.value
        and u.get("email", "").lower() != admin_email
    ]
    user_ids = [u["_id"] for u in to_delete]
    emails = {u.get("email", "").lower() for u in to_delete}

    orphan_abonnes = await db.abonnes.find(
        {
            "$or": [
                {"utilisateur_id": {"$exists": False}},
                {"utilisateur_id": None},
                {"utilisateur_id": {"$in": user_ids}},
                {"email": {"$in": list(emails)}},
            ]
        }
    ).to_list(length=10_000)
    orphan_abonnes = [
        ab for ab in orphan_abonnes if ab.get("email", "").lower() != admin_email
    ]
    return to_delete, orphan_abonnes


async def _write_backup(
    backup_dir: Path,
    users: list[dict[str, Any]],
    abonnes: list[dict[str, Any]],
) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = backup_dir / f"purge_backup_{stamp}.json"
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "admin_email": settings.admin_email,
        "users": [_serialize_doc(u) for u in users],
        "abonnes": [_serialize_doc(a) for a in abonnes],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


async def main() -> int:
    parser = argparse.ArgumentParser(description="Purge des comptes non administrateurs")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher les comptes concernés sans supprimer",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=BACKEND_ROOT / "backups",
        help="Répertoire de sauvegarde JSON avant suppression",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help=f"Confirmer sans invite (sinon taper {CONFIRMATION_TOKEN})",
    )
    args = parser.parse_args()

    admin_email = (settings.admin_email or "").lower()
    if not admin_email:
        print("Erreur : ADMIN_EMAIL non défini dans .env", file=sys.stderr)
        return 1

    db = get_database()
    to_delete, orphan_abonnes = await _collect_targets(db, admin_email)

    total_users = await db.utilisateurs.count_documents({})
    print(f"Comptes trouvés : {total_users} — à supprimer : {len(to_delete)}")
    print(f"Abonnés orphelins / liés à supprimer : {len(orphan_abonnes)}")

    if not to_delete and not orphan_abonnes:
        print("Rien à supprimer.")
        await close_client()
        return 0

    for user in to_delete:
        print(f"  utilisateur : {user.get('email')}")
    for ab in orphan_abonnes:
        print(f"  abonné      : {ab.get('email')}")

    if args.dry_run:
        print("\n[DRY-RUN] Aucune modification effectuée.")
        await close_client()
        return 0

    if not args.yes:
        print(
            f"\nATTENTION : cette opération est irréversible.\n"
            f"Tapez exactement « {CONFIRMATION_TOKEN} » pour continuer : ",
            end="",
            flush=True,
        )
        if input().strip() != CONFIRMATION_TOKEN:
            print("Annulé.")
            await close_client()
            return 1

    backup_path = await _write_backup(args.backup_dir, to_delete, orphan_abonnes)
    print(f"Sauvegarde écrite : {backup_path}")

    deleted = 0
    for user in to_delete:
        ok = await delete_user_and_data(db, user["_id"], user["email"])
        if ok:
            deleted += 1
            print(f"  supprimé : {user['email']}")

    seen_abonne_ids: set[str] = set()
    for ab in orphan_abonnes:
        ab_id = ab["_id"]
        key = str(ab_id)
        if key in seen_abonne_ids:
            continue
        seen_abonne_ids.add(key)
        await db.notifications_envoyees.delete_many({"abonne_id": ab_id})
        await db.abonnes.delete_one({"_id": ab_id})
        print(f"  abonné orphelin supprimé : {ab.get('email')}")

    remaining = await db.utilisateurs.count_documents({})
    print(f"Terminé — {deleted} compte(s) supprimé(s), {remaining} compte(s) restant(s).")
    await close_client()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
