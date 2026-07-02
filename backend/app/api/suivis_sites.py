"""Suivi de sites par les utilisateurs inscrits."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response

from app.api.deps import CurrentUserDep, DbDep
from app.api.schemas import LogScrapingResponse, SuiviSiteCreateRequest, SuiviSiteResponse
from app.models.enums import ScrapingStatus, ScrapingType
from app.scrapers.registry import run_scraper_for_source

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suivis-sites", tags=["suivis-sites"])

MAX_SITES_PAR_UTILISATEUR = 20


def _normalize_url(url: str) -> str:
    value = url.strip()
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    return value.rstrip("/")


def _domain_from_url(url: str) -> str:
    host = urlparse(url).netloc or url
    return host.replace("www.", "")


def _slug_email(email: str) -> str:
    local = email.split("@")[0]
    return re.sub(r"[^a-zA-Z0-9_-]", "", local)[:24] or "user"


def _run_scraper_background(source_id: str) -> None:
    from pymongo import MongoClient

    from app.db.config import settings

    client = MongoClient(settings.mongodb_uri)
    try:
        db = client[settings.mongodb_db_name]
        source = db.sources.find_one({"_id": ObjectId(source_id)})
        if source:
            run_scraper_for_source(source)
    except Exception as exc:
        logger.error("Scraping asynchrone échoué pour %s : %s", source_id, exc)
    finally:
        client.close()


async def _build_nom(db, user_id: ObjectId, url: str, email: str) -> str:
    base = _domain_from_url(url)
    conflict = await db.sources.find_one(
        {"nom": base, "utilisateur_id": {"$ne": user_id}}
    )
    if conflict:
        return f"{base} ({_slug_email(email)})"
    return base


async def _source_to_response(db, source: dict) -> SuiviSiteResponse:
    last_log = await db.logs_scraping.find_one(
        {"source_id": source["_id"]},
        sort=[("date_execution", -1)],
    )
    return SuiviSiteResponse(
        id=str(source["_id"]),
        nom=source["nom"],
        url_base=source["url_base"],
        actif=source.get("actif", True),
        derniere_execution=source.get("derniere_execution"),
        dernier_statut=ScrapingStatus(last_log["statut"]) if last_log else None,
        nb_offres_trouvees=last_log.get("nb_offres_trouvees") if last_log else None,
        nb_offres_nouvelles=last_log.get("nb_offres_nouvelles") if last_log else None,
        message_erreur=last_log.get("message_erreur") if last_log else None,
        date_creation=source.get("date_creation"),
    )


@router.get(
    "",
    response_model=list[SuiviSiteResponse],
    summary="Mes sites suivis",
)
async def list_suivis_sites(
    user: CurrentUserDep,
    db: DbDep,
) -> list[SuiviSiteResponse]:
    docs = (
        await db.sources.find({"utilisateur_id": user.id})
        .sort("date_creation", -1)
        .to_list(length=None)
    )
    return [await _source_to_response(db, doc) for doc in docs]


@router.post(
    "",
    response_model=SuiviSiteResponse,
    status_code=201,
    summary="Ajouter un site à suivre",
    description="Enregistre l'URL et lance un premier scraping en arrière-plan.",
)
async def create_suivi_site(
    payload: SuiviSiteCreateRequest,
    user: CurrentUserDep,
    db: DbDep,
    background_tasks: BackgroundTasks,
) -> SuiviSiteResponse:
    url = _normalize_url(str(payload.url))
    if not urlparse(url).netloc:
        raise HTTPException(status_code=400, detail="URL invalide")

    existing = await db.sources.find_one(
        {"utilisateur_id": user.id, "url_base": url}
    )
    if existing:
        raise HTTPException(status_code=409, detail="Vous suivez déjà ce site")

    count = await db.sources.count_documents({"utilisateur_id": user.id})
    if count >= MAX_SITES_PAR_UTILISATEUR:
        raise HTTPException(
            status_code=400,
            detail=f"Limite de {MAX_SITES_PAR_UTILISATEUR} sites suivis atteinte",
        )

    nom = await _build_nom(db, user.id, url, user.email)
    now = datetime.now(timezone.utc)
    doc = {
        "nom": nom,
        "pays": payload.pays or "—",
        "url_base": url,
        "type_scraping": ScrapingType.HTML.value,
        "actif": True,
        "config": {},
        "utilisateur_id": user.id,
        "date_creation": now,
        "derniere_execution": None,
    }
    result = await db.sources.insert_one(doc)
    doc["_id"] = result.inserted_id

    background_tasks.add_task(_run_scraper_background, str(doc["_id"]))

    return await _source_to_response(db, doc)


@router.post(
    "/{site_id}/scraping",
    response_model=dict,
    summary="Relancer le scraping d'un site suivi",
)
async def refresh_suivi_site(
    site_id: str,
    user: CurrentUserDep,
    db: DbDep,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    if not ObjectId.is_valid(site_id):
        raise HTTPException(status_code=400, detail="Identifiant invalide")

    source = await db.sources.find_one(
        {"_id": ObjectId(site_id), "utilisateur_id": user.id}
    )
    if not source:
        raise HTTPException(status_code=404, detail="Site introuvable")

    if not source.get("actif", True):
        raise HTTPException(status_code=400, detail="Ce site est désactivé")

    background_tasks.add_task(_run_scraper_background, site_id)
    return {"statut": "en_cours", "message": "Analyse lancée en arrière-plan"}


@router.delete(
    "/{site_id}",
    status_code=204,
    summary="Arrêter le suivi d'un site",
)
async def delete_suivi_site(
    site_id: str,
    user: CurrentUserDep,
    db: DbDep,
) -> Response:
    if not ObjectId.is_valid(site_id):
        raise HTTPException(status_code=400, detail="Identifiant invalide")

    result = await db.sources.delete_one(
        {"_id": ObjectId(site_id), "utilisateur_id": user.id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Site introuvable")
    return Response(status_code=204)
