from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import hash_password
from app.db.config import settings
from app.models.enums import UserRole
from app.services.abonne_prefs import ensure_abonne_linked_to_user, get_abonne_for_user
from app.db.sector_seed import SECTEUR_SEED_DATA
from app.scrapers.sources_config import SCRAPER_SOURCES


async def ensure_sectors(db: AsyncIOMotorDatabase) -> None:
    """Crée les secteurs de référence s'ils sont absents (classification automatique)."""
    count = await db.secteurs.count_documents({})
    if count > 0:
        return
    await db.secteurs.insert_many(SECTEUR_SEED_DATA)


async def ensure_admin_user(db: AsyncIOMotorDatabase) -> None:
    if not settings.admin_email or not settings.admin_password:
        return

    email = settings.admin_email.lower()
    existing = await db.utilisateurs.find_one({"email": email})
    if existing:
        return

    await db.utilisateurs.insert_one(
        {
            "email": email,
            "mot_de_passe_hash": hash_password(settings.admin_password),
            "role": UserRole.ADMIN.value,
            "auth_provider": "email",
            "email_verifie": True,
            "statut_email": "verifie",
            "date_verification_email": datetime.now(timezone.utc),
            "date_inscription": datetime.now(timezone.utc),
        }
    )


async def ensure_notification_abonnes(db: AsyncIOMotorDatabase) -> None:
    """Lie chaque compte utilisateur à un profil d'alertes email."""
    async for user in db.utilisateurs.find({}, {"_id": 1, "email": 1, "role": 1}):
        await ensure_abonne_linked_to_user(db, user["_id"], user["email"])
        linked = await get_abonne_for_user(db, user["_id"], user["email"])
        if not linked:
            continue
        if user.get("role") == UserRole.ADMIN.value:
            await db.abonnes.update_one(
                {"_id": linked["_id"]},
                {"$set": {"preferences_configurees": True}},
            )
            continue
        secteurs = linked.get("secteurs_suivis") or []
        pays = linked.get("pays_suivis") or []
        if secteurs and pays:
            await db.abonnes.update_one(
                {"_id": linked["_id"]},
                {"$set": {"preferences_configurees": True, "utilisateur_id": user["_id"]}},
            )


async def ensure_scraper_sources(db: AsyncIOMotorDatabase) -> None:
    """Crée ou met à jour les sources officielles (sans supprimer les sources admin)."""
    for source in SCRAPER_SOURCES:
        doc = {
            "nom": source["nom"],
            "pays": source["pays"],
            "url_base": source["url_base"],
            "type_scraping": source["type_scraping"],
            "actif": source.get("actif", True),
        }
        if source.get("config"):
            doc["config"] = source["config"]
        existing = await db.sources.find_one(
            {"nom": source["nom"], "utilisateur_id": {"$exists": False}}
        )
        if existing:
            await db.sources.update_one({"_id": existing["_id"]}, {"$set": doc})
        else:
            doc["derniere_execution"] = None
            await db.sources.insert_one(doc)
