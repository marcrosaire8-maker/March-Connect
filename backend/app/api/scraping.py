from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.api.deps import AdminUserDep, DbDep
from app.api.schemas import ScrapingTriggerRequest, ScrapingTriggerResponse
from app.models.enums import ScrapingStatus
from app.scrapers.registry import run_scraper_for_source

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post(
    "/trigger",
    response_model=ScrapingTriggerResponse,
    summary="Déclencher manuellement le scraper d'une source",
    description=(
        "Lance le scraper associé à la source indiquée. "
        "L'opération peut prendre plusieurs minutes selon le volume de données."
    ),
)
async def trigger_scraping(
    payload: ScrapingTriggerRequest,
    db: DbDep,
    _admin: AdminUserDep,
) -> ScrapingTriggerResponse:
    source = await db.sources.find_one({"_id": ObjectId(payload.source_id)})
    if not source:
        raise HTTPException(status_code=404, detail="Source introuvable")

    if not source.get("actif", True):
        raise HTTPException(status_code=400, detail="Cette source est désactivée")

    result = run_scraper_for_source(source)

    return ScrapingTriggerResponse(
        source_id=payload.source_id,
        source_nom=source["nom"],
        statut=ScrapingStatus(result["statut"]),
        nb_offres_trouvees=result["nb_offres_trouvees"],
        nb_offres_nouvelles=result["nb_offres_nouvelles"],
        message_erreur=result.get("message_erreur"),
    )
