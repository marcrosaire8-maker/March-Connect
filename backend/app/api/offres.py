import calendar
import math
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUserDep, DbDep
from app.api.schemas import (
    CalendrierJourResponse,
    CalendrierOffreItem,
    CalendrierOffresResponse,
    OffreResponse,
    PaginatedOffresResponse,
)
from app.services.abonne_prefs import (
    abonne_has_active_preferences,
    abonne_preference_lists,
    get_abonne_for_user,
)
from app.services.offre_filters import (
    active_deadline_filter,
    favoris_filter,
    merge_mongo_filters,
    mes_sites_filter,
    offres_list_aggregation_pipeline,
    text_search_filter,
    user_preferences_filter,
)

router = APIRouter(prefix="/offres", tags=["offres"])


def _parse_optional_object_id(value: Optional[str], field_name: str) -> Optional[ObjectId]:
    if value is None:
        return None
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=422, detail=f"{field_name} invalide")
    return ObjectId(value)


def _empty_page(page: int, page_size: int) -> PaginatedOffresResponse:
    return PaginatedOffresResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0,
    )


async def _build_user_query(
    db,
    user,
    *,
    secteur_id: Optional[ObjectId],
    pays: Optional[str],
    source_id: Optional[ObjectId],
    date_limite_apres: Optional[datetime],
    q: Optional[str],
    favoris_only: bool,
    mes_sites_only: bool,
) -> dict | None:
    if user.is_admin:
        query: dict = {}
        if source_id is not None:
            query["source_id"] = source_id
        if secteur_id is not None:
            query["secteur_id"] = secteur_id
        if pays:
            query["pays"] = pays
    else:
        abonne = await get_abonne_for_user(db, user.id, user.email)
        if not abonne_has_active_preferences(abonne):
            return None

        secteurs_suivis, pays_suivis = abonne_preference_lists(abonne)
        query = merge_mongo_filters(
            user_preferences_filter(
                secteurs_suivis,
                pays_suivis,
                secteur_id=secteur_id,
                pays=pays or None,
            ),
        )
        if source_id is not None:
            query = merge_mongo_filters(query, {"source_id": source_id})

        if favoris_only:
            fav_ids = await db.favoris.distinct(
                "offre_id",
                {"utilisateur_id": user.id},
            )
            query = merge_mongo_filters(
                query,
                favoris_filter([oid for oid in fav_ids if isinstance(oid, ObjectId)]),
            )

        if mes_sites_only:
            source_ids = await db.sources.distinct(
                "_id",
                {"utilisateur_id": user.id},
            )
            query = merge_mongo_filters(
                query,
                mes_sites_filter([oid for oid in source_ids if isinstance(oid, ObjectId)]),
            )

    if date_limite_apres is not None:
        deadline_clause = active_deadline_filter(
            date_limite_apres,
            include_without_deadline=False,
        )
    else:
        deadline_clause = active_deadline_filter()

    query = merge_mongo_filters(query, deadline_clause, text_search_filter(q))
    return query


@router.get(
    "",
    response_model=PaginatedOffresResponse,
    summary="Liste paginée des offres",
    description="Offres filtrées selon les secteurs et pays choisis dans Mon compte.",
)
async def list_offres(
    db: DbDep,
    user: CurrentUserDep,
    page: int = Query(1, ge=1, description="Numéro de page (à partir de 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Nombre d'offres par page"),
    secteur_id: Optional[str] = Query(None, description="Filtrer par secteur"),
    pays: Optional[str] = Query(None, description="Filtrer par pays"),
    source_id: Optional[str] = Query(None, description="Filtrer par source"),
    q: Optional[str] = Query(None, description="Recherche texte (titre, organisme, description)"),
    favoris_only: bool = Query(False, description="Uniquement les favoris"),
    mes_sites_only: bool = Query(False, description="Uniquement les offres de mes sites"),
    date_limite_apres: Optional[datetime] = Query(
        None,
        description="Offres dont la date limite est postérieure ou égale à cette date",
    ),
) -> PaginatedOffresResponse:
    parsed_secteur = _parse_optional_object_id(secteur_id, "secteur_id")
    parsed_source = _parse_optional_object_id(source_id, "source_id")

    query = await _build_user_query(
        db,
        user,
        secteur_id=parsed_secteur,
        pays=pays,
        source_id=parsed_source,
        date_limite_apres=date_limite_apres,
        q=q,
        favoris_only=favoris_only,
        mes_sites_only=mes_sites_only,
    )
    if query is None:
        return _empty_page(page, page_size)

    total = await db.offres.count_documents(query)
    skip = (page - 1) * page_size

    pipeline = offres_list_aggregation_pipeline(query, skip=skip, limit=page_size)
    docs = await db.offres.aggregate(pipeline).to_list(length=page_size)

    return PaginatedOffresResponse(
        items=[OffreResponse.from_mongo(doc) for doc in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)) if total else 0,
    )


@router.get(
    "/calendrier",
    response_model=CalendrierOffresResponse,
    summary="Calendrier des échéances",
)
async def calendrier_offres(
    db: DbDep,
    user: CurrentUserDep,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> CalendrierOffresResponse:
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day = calendar.monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    query = await _build_user_query(
        db,
        user,
        secteur_id=None,
        pays=None,
        source_id=None,
        date_limite_apres=None,
        q=None,
        favoris_only=False,
        mes_sites_only=False,
    )
    if query is None:
        return CalendrierOffresResponse(year=year, month=month, jours=[], total=0)

    query = merge_mongo_filters(
        query,
        {"date_limite": {"$gte": start, "$lte": end}},
    )

    docs = await db.offres.find(
        query,
        {
            "_id": 1,
            "titre": 1,
            "organisme": 1,
            "pays": 1,
            "date_limite": 1,
        },
    ).sort("date_limite", 1).to_list(length=500)

    grouped: dict[str, list[CalendrierOffreItem]] = {}
    for doc in docs:
        date_limite = doc.get("date_limite")
        if not isinstance(date_limite, datetime):
            continue
        key = date_limite.astimezone(timezone.utc).strftime("%Y-%m-%d")
        grouped.setdefault(key, []).append(
            CalendrierOffreItem(
                id=str(doc["_id"]),
                titre=doc.get("titre", ""),
                organisme=doc.get("organisme", ""),
                pays=doc.get("pays", ""),
                date_limite=date_limite,
            )
        )

    jours = [
        CalendrierJourResponse(date=day, offres=items)
        for day, items in sorted(grouped.items())
    ]
    return CalendrierOffresResponse(
        year=year,
        month=month,
        jours=jours,
        total=len(docs),
    )


@router.get(
    "/{offre_id}",
    response_model=OffreResponse,
    summary="Détail d'une offre",
)
async def get_offre(
    offre_id: str,
    db: DbDep,
    user: CurrentUserDep,
) -> OffreResponse:
    if not ObjectId.is_valid(offre_id):
        raise HTTPException(status_code=422, detail="Identifiant d'offre invalide")

    doc = await db.offres.find_one({"_id": ObjectId(offre_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Offre introuvable")

    if not user.is_admin:
        abonne = await get_abonne_for_user(db, user.id, user.email)
        if not abonne_has_active_preferences(abonne):
            raise HTTPException(status_code=403, detail="Préférences non configurées")

        secteurs_suivis, pays_suivis = abonne_preference_lists(abonne)
        offre_pays = doc.get("pays")
        offre_secteur = doc.get("secteur_id")

        if offre_pays not in pays_suivis:
            raise HTTPException(status_code=404, detail="Offre introuvable")

        secteur_ids = {str(s) for s in secteurs_suivis}
        if offre_secteur is None or str(offre_secteur) not in secteur_ids:
            raise HTTPException(status_code=404, detail="Offre introuvable")

    return OffreResponse.from_mongo(doc)
