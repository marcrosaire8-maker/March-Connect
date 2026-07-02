from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING


def _has_index(indexes: dict, key: list, unique: bool | None = None) -> bool:
    for info in indexes.values():
        if info.get("key") == key:
            if unique is None or info.get("unique") == unique:
                return True
    return False


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    offres_indexes = await db.offres.index_information()
    if not _has_index(offres_indexes, [("hash_unique", 1)], unique=True):
        await db.offres.create_index(
            [("hash_unique", ASCENDING)], unique=True, name="hash_unique"
        )
    if not _has_index(offres_indexes, [("secteur_id", 1)]):
        await db.offres.create_index([("secteur_id", ASCENDING)])
    if not _has_index(offres_indexes, [("pays", 1)]):
        await db.offres.create_index([("pays", ASCENDING)])
    if not _has_index(offres_indexes, [("source_id", 1), ("external_id", 1)], unique=True):
        await db.offres.create_index(
            [("source_id", ASCENDING), ("external_id", ASCENDING)],
            unique=True,
            partialFilterExpression={"external_id": {"$exists": True}},
            name="source_external_id_unique",
        )
    if not _has_index(offres_indexes, [("date_scraping", 1)]):
        await db.offres.create_index([("date_scraping", ASCENDING)])
    if not _has_index(offres_indexes, [("date_scraping", 1), ("date_publication", 1)]):
        await db.offres.create_index(
            [("date_scraping", ASCENDING), ("date_publication", ASCENDING)],
            name="offres_scraping_publication",
        )

    logs_indexes = await db.logs_scraping.index_information()
    if not _has_index(logs_indexes, [("source_id", 1)]):
        await db.logs_scraping.create_index([("source_id", ASCENDING)])
    if not _has_index(logs_indexes, [("date_execution", 1)]):
        await db.logs_scraping.create_index([("date_execution", ASCENDING)])

    sources_indexes = await db.sources.index_information()
    if not _has_index(sources_indexes, [("pays", 1)]):
        await db.sources.create_index([("pays", ASCENDING)])
    if not _has_index(sources_indexes, [("utilisateur_id", 1)]):
        await db.sources.create_index([("utilisateur_id", ASCENDING)])
    if not _has_index(sources_indexes, [("utilisateur_id", 1), ("url_base", 1)], unique=True):
        await db.sources.create_index(
            [("utilisateur_id", ASCENDING), ("url_base", ASCENDING)],
            unique=True,
            partialFilterExpression={"utilisateur_id": {"$exists": True}},
            name="utilisateur_url_unique",
        )

    secteurs_indexes = await db.secteurs.index_information()
    if not _has_index(secteurs_indexes, [("nom", 1)], unique=True):
        await db.secteurs.create_index([("nom", ASCENDING)], unique=True)

    abonnes_indexes = await db.abonnes.index_information()
    if not _has_index(abonnes_indexes, [("email", 1)], unique=True):
        await db.abonnes.create_index([("email", ASCENDING)], unique=True)
    if not _has_index(abonnes_indexes, [("actif", 1)]):
        await db.abonnes.create_index([("actif", ASCENDING)])

    logs_notif_indexes = await db.logs_notifications.index_information()
    if not _has_index(logs_notif_indexes, [("date_execution", 1)]):
        await db.logs_notifications.create_index([("date_execution", ASCENDING)])

    notif_sent_indexes = await db.notifications_envoyees.index_information()
    if not _has_index(
        notif_sent_indexes, [("abonne_id", 1), ("offre_id", 1)], unique=True
    ):
        await db.notifications_envoyees.create_index(
            [("abonne_id", ASCENDING), ("offre_id", ASCENDING)],
            unique=True,
            name="abonne_offre_unique",
        )
    if not _has_index(notif_sent_indexes, [("date_envoi", 1)]):
        await db.notifications_envoyees.create_index([("date_envoi", ASCENDING)])

    favoris_indexes = await db.favoris.index_information()
    if not _has_index(
        favoris_indexes, [("utilisateur_id", 1), ("offre_id", 1)], unique=True
    ):
        await db.favoris.create_index(
            [("utilisateur_id", ASCENDING), ("offre_id", ASCENDING)],
            unique=True,
            name="utilisateur_offre_unique",
        )

    rappels_indexes = await db.rappels_envoyes.index_information()
    if not _has_index(
        rappels_indexes,
        [("abonne_id", 1), ("offre_id", 1), ("jours_avant", 1)],
        unique=True,
    ):
        await db.rappels_envoyes.create_index(
            [
                ("abonne_id", ASCENDING),
                ("offre_id", ASCENDING),
                ("jours_avant", ASCENDING),
            ],
            unique=True,
            name="rappel_unique",
        )

    users_indexes = await db.utilisateurs.index_information()
    if not _has_index(users_indexes, [("email", 1)], unique=True):
        await db.utilisateurs.create_index([("email", ASCENDING)], unique=True)
    if not _has_index(users_indexes, [("google_id", 1)], unique=True):
        await db.utilisateurs.create_index(
            [("google_id", ASCENDING)],
            unique=True,
            sparse=True,
            name="google_id_unique",
        )
    if not _has_index(users_indexes, [("apple_id", 1)], unique=True):
        await db.utilisateurs.create_index(
            [("apple_id", ASCENDING)],
            unique=True,
            sparse=True,
            name="apple_id_unique",
        )

    otp_indexes = await db.password_reset_otps.index_information()
    if not _has_index(otp_indexes, [("email", 1)], unique=True):
        await db.password_reset_otps.create_index(
            [("email", ASCENDING)], unique=True, name="email_unique"
        )
    if not _has_index(otp_indexes, [("expires_at", 1)]):
        await db.password_reset_otps.create_index(
            [("expires_at", ASCENDING)], expireAfterSeconds=0, name="expires_at_ttl"
        )

    email_otp_indexes = await db.email_verification_otps.index_information()
    if not _has_index(email_otp_indexes, [("email", 1)], unique=True):
        await db.email_verification_otps.create_index(
            [("email", ASCENDING)], unique=True, name="email_verification_unique"
        )
    if not _has_index(email_otp_indexes, [("expires_at", 1)]):
        await db.email_verification_otps.create_index(
            [("expires_at", ASCENDING)],
            expireAfterSeconds=0,
            name="email_verification_expires_ttl",
        )

    if not _has_index(abonnes_indexes, [("utilisateur_id", 1)]):
        await db.abonnes.create_index([("utilisateur_id", ASCENDING)])
