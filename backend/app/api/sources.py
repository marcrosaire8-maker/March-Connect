from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.deps import AdminUserDep, DbDep
from app.api.schemas import SourceCreateRequest, SourceResponse

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get(
    "",
    response_model=list[SourceResponse],
    summary="Liste des sources de scraping (admin)",
)
async def list_sources(
    db: DbDep,
    _admin: AdminUserDep,
) -> list[SourceResponse]:
    docs = (
        await db.sources.find({"utilisateur_id": {"$exists": False}})
        .sort("nom", 1)
        .to_list(length=None)
    )
    return [SourceResponse.from_mongo(doc) for doc in docs]


@router.post(
    "",
    response_model=SourceResponse,
    status_code=201,
    summary="Ajouter une source de scraping (admin)",
    description=(
        "Enregistre une nouvelle source. Le scraping utilise automatiquement "
        "le scraper générique (HTML, API ou RSS selon type_scraping)."
    ),
)
async def create_source(
    payload: SourceCreateRequest,
    db: DbDep,
    _admin: AdminUserDep,
) -> SourceResponse:
    existing = await db.sources.find_one({"nom": payload.nom})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Une source nommée « {payload.nom} » existe déjà",
        )

    doc = {
        "nom": payload.nom,
        "pays": payload.pays,
        "url_base": str(payload.url_base).rstrip("/"),
        "type_scraping": payload.type_scraping.value,
        "actif": payload.actif,
        "config": payload.config,
        "derniere_execution": None,
    }
    result = await db.sources.insert_one(doc)
    doc["_id"] = result.inserted_id
    return SourceResponse.from_mongo(doc)
