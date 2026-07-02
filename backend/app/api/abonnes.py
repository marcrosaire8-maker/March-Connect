from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Request
from pymongo.errors import DuplicateKeyError

from app.api.deps import CurrentUserDep, DbDep
from app.api.schemas import (
    AbonneCreateRequest,
    AbonneEmailRequest,
    AbonneResponse,
    UnsubscribeEmailRequest,
)
from app.core.rate_limit import LIMIT_UNSUBSCRIBE, limiter
from app.services.abonne_prefs import (
    abonne_has_active_preferences,
    abonne_preference_lists,
    consolidate_user_abonne,
    get_abonne_for_user,
    offre_matches_keywords,
)
from app.services.transactional_email import send_alerts_activated_email_safe

router = APIRouter(prefix="/abonnes", tags=["abonnes"])

MAX_EMAILS_SUPPLEMENTAIRES = 5
MAX_MOTS_CLES = 20


def _normalize_keywords(values: list[str]) -> list[str]:
    keywords: list[str] = []
    for raw in values:
        value = str(raw).strip()
        if not value:
            continue
        if len(value) > 80:
            value = value[:80]
        if value.lower() not in {k.lower() for k in keywords}:
            keywords.append(value)
        if len(keywords) >= MAX_MOTS_CLES:
            break
    return keywords


async def _criteria_label_from_abonne(db, abonne: dict) -> str:
    secteurs, pays = abonne_preference_lists(abonne)
    secteur_names: list[str] = []
    if secteurs:
        async for doc in db.secteurs.find({"_id": {"$in": secteurs}}, {"nom": 1}):
            secteur_names.append(doc.get("nom") or "Secteur")
    parts: list[str] = []
    if secteur_names:
        parts.append(" · ".join(secteur_names))
    if pays:
        parts.append(" · ".join(pays))
    return " · ".join(parts) if parts else "Vos critères"


async def _email_already_used(db, email: str, utilisateur_id: ObjectId) -> bool:
    other_primary = await db.abonnes.find_one(
        {"email": email, "utilisateur_id": {"$ne": utilisateur_id}}
    )
    if other_primary:
        return True
    other_extra = await db.abonnes.find_one(
        {
            "emails_supplementaires": email,
            "utilisateur_id": {"$ne": utilisateur_id},
        }
    )
    return other_extra is not None


async def _get_or_create_abonne(user: CurrentUserDep, db: DbDep) -> dict:
    existing = await get_abonne_for_user(db, user.id, user.email)
    if existing:
        return existing

    doc = {
        "email": user.email.lower(),
        "utilisateur_id": user.id,
        "secteurs_suivis": [],
        "pays_suivis": [],
        "emails_supplementaires": [],
        "mots_cles_alertes": [],
        "preferences_configurees": False,
        "actif": True,
        "date_inscription": datetime.now(timezone.utc),
    }
    result = await db.abonnes.insert_one(doc)
    created = await db.abonnes.find_one({"_id": result.inserted_id})
    assert created is not None
    return created


@router.get(
    "/me",
    response_model=AbonneResponse | None,
    summary="Préférences de notification de l'utilisateur connecté",
)
async def get_my_abonne(user: CurrentUserDep, db: DbDep) -> AbonneResponse | None:
    doc = await get_abonne_for_user(db, user.id, user.email)
    if not doc:
        return None
    return AbonneResponse.from_mongo(doc)


@router.post(
    "",
    response_model=AbonneResponse,
    status_code=201,
    summary="Enregistrer les secteurs et pays suivis",
)
async def create_abonne(
    payload: AbonneCreateRequest,
    user: CurrentUserDep,
    db: DbDep,
) -> AbonneResponse:
    if not payload.secteurs_suivis or not payload.pays_suivis:
        raise HTTPException(
            status_code=422,
            detail="Choisissez au moins un secteur et un pays",
        )

    secteur_ids = [ObjectId(s) for s in payload.secteurs_suivis]
    found = await db.secteurs.count_documents({"_id": {"$in": secteur_ids}})
    if found != len(secteur_ids):
        raise HTTPException(
            status_code=422,
            detail="Un ou plusieurs secteurs_suivis sont invalides",
        )

    email = user.email.lower()
    existing = await get_abonne_for_user(db, user.id, email)
    was_configured = abonne_has_active_preferences(existing)
    now = datetime.now(timezone.utc)

    preferences_configurees = True
    keywords = _normalize_keywords(payload.mots_cles_alertes)

    doc = {
        "email": email,
        "utilisateur_id": user.id,
        "secteurs_suivis": secteur_ids,
        "pays_suivis": payload.pays_suivis,
        "mots_cles_alertes": keywords,
        "preferences_configurees": preferences_configurees,
        "actif": True,
        "date_maj": now,
    }

    if existing:
        await db.abonnes.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "secteurs_suivis": secteur_ids,
                    "pays_suivis": payload.pays_suivis,
                    "mots_cles_alertes": keywords,
                    "preferences_configurees": True,
                    "actif": True,
                    "email": email,
                    "utilisateur_id": user.id,
                    "date_maj": now,
                },
                "$setOnInsert": {"emails_supplementaires": []},
            },
        )
        consolidated = await consolidate_user_abonne(db, user.id, email)
        assert consolidated is not None
        if not was_configured:
            label = await _criteria_label_from_abonne(db, consolidated)
            send_alerts_activated_email_safe(email, label)
        return AbonneResponse.from_mongo(consolidated)

    doc["emails_supplementaires"] = []
    doc["date_inscription"] = now

    try:
        result = await db.abonnes.insert_one(doc)
    except DuplicateKeyError:
        by_email = await db.abonnes.find_one({"email": email})
        if by_email:
            await db.abonnes.update_one(
                {"_id": by_email["_id"]},
                {"$set": doc},
            )
            consolidated = await consolidate_user_abonne(db, user.id, email)
            assert consolidated is not None
            if not was_configured:
                label = await _criteria_label_from_abonne(db, consolidated)
                send_alerts_activated_email_safe(email, label)
            return AbonneResponse.from_mongo(consolidated)
        raise HTTPException(
            status_code=409,
            detail="Cet email est déjà inscrit aux alertes",
        ) from None

    consolidated = await consolidate_user_abonne(db, user.id, email)
    assert consolidated is not None
    if not was_configured:
        label = await _criteria_label_from_abonne(db, consolidated)
        send_alerts_activated_email_safe(email, label)
    return AbonneResponse.from_mongo(consolidated)


@router.post(
    "/emails",
    response_model=AbonneResponse,
    summary="Ajouter un email supplémentaire pour les alertes",
)
async def add_abonne_email(
    payload: AbonneEmailRequest,
    user: CurrentUserDep,
    db: DbDep,
) -> AbonneResponse:
    email = str(payload.email).lower()
    if email == user.email.lower():
        raise HTTPException(
            status_code=422,
            detail="Cet email est déjà celui de votre compte",
        )

    abonne = await _get_or_create_abonne(user, db)
    extras = abonne.get("emails_supplementaires", [])
    if email in extras:
        raise HTTPException(status_code=409, detail="Cet email est déjà ajouté")

    if len(extras) >= MAX_EMAILS_SUPPLEMENTAIRES:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {MAX_EMAILS_SUPPLEMENTAIRES} emails supplémentaires",
        )

    if await _email_already_used(db, email, user.id):
        raise HTTPException(
            status_code=409,
            detail="Cet email est déjà utilisé par un autre compte",
        )

    existing_user = await db.utilisateurs.find_one({"email": email})
    if existing_user and existing_user["_id"] != user.id:
        raise HTTPException(
            status_code=409,
            detail="Cet email est déjà associé à un autre compte",
        )

    await db.abonnes.update_one(
        {"_id": abonne["_id"]},
        {"$addToSet": {"emails_supplementaires": email}},
    )
    updated = await db.abonnes.find_one({"_id": abonne["_id"]})
    return AbonneResponse.from_mongo(updated)


@router.delete(
    "/emails",
    response_model=AbonneResponse,
    summary="Retirer un email supplémentaire des alertes",
)
async def remove_abonne_email(
    user: CurrentUserDep,
    db: DbDep,
    email: str = Query(..., min_length=3),
) -> AbonneResponse:
    normalized = email.lower()
    abonne = await db.abonnes.find_one({"utilisateur_id": user.id, "actif": True})
    if not abonne:
        raise HTTPException(status_code=404, detail="Aucune préférence d'alerte")

    extras = abonne.get("emails_supplementaires", [])
    if normalized not in extras:
        raise HTTPException(status_code=404, detail="Email introuvable")

    await db.abonnes.update_one(
        {"_id": abonne["_id"]},
        {"$pull": {"emails_supplementaires": normalized}},
    )
    updated = await db.abonnes.find_one({"_id": abonne["_id"]})
    return AbonneResponse.from_mongo(updated)


@router.post(
    "/unsubscribe",
    summary="Se désinscrire des alertes par e-mail (public)",
)
@limiter.limit(LIMIT_UNSUBSCRIBE)
async def unsubscribe_by_email(
    request: Request,
    db: DbDep,
    payload: UnsubscribeEmailRequest,
) -> dict[str, str]:
    email = payload.email.lower().strip()
    await db.abonnes.update_many(
        {
            "$or": [{"email": email}, {"emails_supplementaires": email}],
            "actif": True,
        },
        {"$set": {"actif": False}},
    )
    return {
        "message": (
            "Si cette adresse était inscrite aux alertes, elle a été désinscrite avec succès."
        ),
    }


@router.delete(
    "/{abonne_id}",
    status_code=204,
    summary="Se désinscrire des alertes email",
)
async def delete_abonne(
    abonne_id: str,
    user: CurrentUserDep,
    db: DbDep,
) -> None:
    if not ObjectId.is_valid(abonne_id):
        raise HTTPException(status_code=422, detail="Identifiant d'abonné invalide")

    abonne = await db.abonnes.find_one({"_id": ObjectId(abonne_id)})
    if not abonne:
        raise HTTPException(status_code=404, detail="Abonné introuvable")

    if abonne.get("utilisateur_id") != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    await db.abonnes.update_one(
        {"_id": ObjectId(abonne_id)},
        {"$set": {"actif": False}},
    )
