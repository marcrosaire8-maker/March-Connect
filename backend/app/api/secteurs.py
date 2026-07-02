from fastapi import APIRouter

from app.api.deps import DbDep
from app.api.schemas import SecteurResponse
from app.services.offre_filters import active_deadline_filter, merge_mongo_filters

router = APIRouter(prefix="/secteurs", tags=["secteurs"])


@router.get(
    "",
    response_model=list[SecteurResponse],
    summary="Liste des secteurs avec compteur d'offres actives",
    description=(
        "Une offre est considérée active si sa date limite est dans le futur "
        "ou si aucune date limite n'est renseignée."
    ),
)
async def list_secteurs(db: DbDep) -> list[SecteurResponse]:
    pipeline = [
        {
            "$match": merge_mongo_filters(
                active_deadline_filter(),
                {"secteur_id": {"$ne": None}},
            )
        },
        {"$group": {"_id": "$secteur_id", "count": {"$sum": 1}}},
    ]

    counts: dict[str, int] = {}
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
