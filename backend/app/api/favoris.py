"""Favoris utilisateur (offres sauvegardées)."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Response

from app.api.deps import CurrentUserDep, DbDep
from app.services.abonne_prefs import (
    abonne_has_active_preferences,
    abonne_preference_lists,
    get_abonne_for_user,
)

router = APIRouter(prefix="/favoris", tags=["favoris"])


async def _offre_accessible(
    db,
    user,
    offre_id: ObjectId,
) -> bool:
    if user.is_admin:
        return await db.offres.find_one({"_id": offre_id}) is not None

    abonne = await get_abonne_for_user(db, user.id, user.email)
    if not abonne_has_active_preferences(abonne):
        return False

    doc = await db.offres.find_one({"_id": offre_id})
    if not doc:
        return False

    secteurs_suivis, pays_suivis = abonne_preference_lists(abonne)
    if doc.get("pays") not in pays_suivis:
        return False
    secteur_ids = {str(s) for s in secteurs_suivis}
    offre_secteur = doc.get("secteur_id")
    return offre_secteur is not None and str(offre_secteur) in secteur_ids


@router.get(
    "",
    response_model=list[str],
    summary="Identifiants des offres favorites",
)
async def list_favoris(user: CurrentUserDep, db: DbDep) -> list[str]:
    ids = await db.favoris.distinct(
        "offre_id",
        {"utilisateur_id": user.id},
    )
    return [str(oid) for oid in ids if isinstance(oid, ObjectId)]


@router.post(
    "/{offre_id}",
    status_code=201,
    summary="Ajouter une offre aux favoris",
)
async def add_favori(
    offre_id: str,
    user: CurrentUserDep,
    db: DbDep,
) -> dict[str, str]:
    if not ObjectId.is_valid(offre_id):
        raise HTTPException(status_code=422, detail="Identifiant d'offre invalide")

    oid = ObjectId(offre_id)
    if not await _offre_accessible(db, user, oid):
        raise HTTPException(status_code=404, detail="Offre introuvable")

    now = datetime.now(timezone.utc)
    await db.favoris.update_one(
        {"utilisateur_id": user.id, "offre_id": oid},
        {
            "$set": {"date_ajout": now},
            "$setOnInsert": {
                "utilisateur_id": user.id,
                "offre_id": oid,
            },
        },
        upsert=True,
    )
    return {"offre_id": offre_id, "statut": "ajoute"}


@router.delete(
    "/{offre_id}",
    status_code=204,
    summary="Retirer une offre des favoris",
)
async def remove_favori(
    offre_id: str,
    user: CurrentUserDep,
    db: DbDep,
) -> Response:
    if not ObjectId.is_valid(offre_id):
        raise HTTPException(status_code=422, detail="Identifiant d'offre invalide")

    await db.favoris.delete_one(
        {
            "utilisateur_id": user.id,
            "offre_id": ObjectId(offre_id),
        }
    )
    return Response(status_code=204)
