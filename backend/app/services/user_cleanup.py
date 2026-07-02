"""Suppression d'un utilisateur et de toutes ses données associées."""

from __future__ import annotations

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def delete_user_and_data(
    db: AsyncIOMotorDatabase,
    user_id: ObjectId,
    email: str,
) -> bool:
    """Supprime le compte et les données liées. Retourne False si utilisateur introuvable."""
    user = await db.utilisateurs.find_one({"_id": user_id})
    if not user:
        return False

    normalized_email = email.lower()
    source_ids = await db.sources.distinct("_id", {"utilisateur_id": user_id})
    if source_ids:
        await db.offres.delete_many({"source_id": {"$in": source_ids}})
        await db.logs_scraping.delete_many({"source_id": {"$in": source_ids}})
        await db.sources.delete_many({"utilisateur_id": user_id})

    abonne_ids = await db.abonnes.distinct(
        "_id",
        {
            "$or": [
                {"utilisateur_id": user_id},
                {"email": normalized_email},
            ]
        },
    )
    if abonne_ids:
        await db.notifications_envoyees.delete_many({"abonne_id": {"$in": abonne_ids}})

    await db.abonnes.delete_many(
        {
            "$or": [
                {"utilisateur_id": user_id},
                {"email": normalized_email},
            ]
        }
    )
    await db.utilisateurs.delete_one({"_id": user_id})
    return True
