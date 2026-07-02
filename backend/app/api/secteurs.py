from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import CurrentUserDep, DbDep
from app.api.offres import build_offres_query
from app.api.schemas import SecteurResponse
from app.services.offre_filters import merge_mongo_filters

router = APIRouter(prefix="/secteurs", tags=["secteurs"])


@router.get(
    "",
    response_model=list[SecteurResponse],
    summary="Liste des secteurs avec compteur d'offres actives",
    description=(
        "Compteurs alignés sur la même sélection que la liste des offres "
        "(secteurs et pays du compte, filtres actifs de la page)."
    ),
)
async def list_secteurs(
    db: DbDep,
    user: CurrentUserDep,
    pays: Optional[str] = Query(None, description="Filtrer par pays"),
    q: Optional[str] = Query(None, description="Recherche texte"),
    favoris_only: bool = Query(False, description="Uniquement les favoris"),
    mes_sites_only: bool = Query(False, description="Uniquement les offres de mes sites"),
    date_limite_apres: Optional[datetime] = Query(
        None,
        description="Offres dont la date limite est postérieure ou égale à cette date",
    ),
) -> list[SecteurResponse]:
    query = await build_offres_query(
        db,
        user,
        secteur_id=None,
        pays=pays,
        source_id=None,
        date_limite_apres=date_limite_apres,
        q=q,
        favoris_only=favoris_only,
        mes_sites_only=mes_sites_only,
    )

    counts: dict[str, int] = {}
    if query is not None:
        pipeline = [
            {
                "$match": merge_mongo_filters(
                    query,
                    {"secteur_id": {"$ne": None}},
                )
            },
            {"$group": {"_id": "$secteur_id", "count": {"$sum": 1}}},
        ]
        async for row in db.offres.aggregate(pipeline):
            counts[str(row["_id"])] = row["count"]

    secteurs = await db.secteurs.find().sort("nom", 1).to_list(length=None)

    return [
        SecteurResponse.from_mongo(
            secteur,
            nb_offres_actives=counts.get(str(secteur["_id"]), 0),
        )
        for secteur in secteurs
    ]
