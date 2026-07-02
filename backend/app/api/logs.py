from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUserDep, DbDep
from app.api.schemas import LogNotificationResponse, LogScrapingResponse

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get(
    "",
    response_model=list[LogScrapingResponse],
    summary="Historique des exécutions de scraping",
    description="Les exécutions les plus récentes apparaissent en premier.",
)
async def list_logs(
    db: DbDep,
    _admin: AdminUserDep,
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de logs à retourner"),
    source_id: Optional[str] = Query(None, description="Filtrer par source"),
) -> list[LogScrapingResponse]:
    query: dict = {}

    if source_id is not None:
        if not ObjectId.is_valid(source_id):
            raise HTTPException(status_code=422, detail="source_id invalide")
        query["source_id"] = ObjectId(source_id)

    docs = (
        await db.logs_scraping.find(query)
        .sort("date_execution", -1)
        .limit(limit)
        .to_list(length=limit)
    )
    return [LogScrapingResponse.from_mongo(doc) for doc in docs]


@router.get(
    "/notifications",
    response_model=list[LogNotificationResponse],
    summary="Historique des exécutions de notifications (admin)",
)
async def list_notification_logs(
    db: DbDep,
    _admin: AdminUserDep,
    limit: int = Query(50, ge=1, le=200),
) -> list[LogNotificationResponse]:
    docs = (
        await db.logs_notifications.find()
        .sort("date_execution", -1)
        .limit(limit)
        .to_list(length=limit)
    )
    return [LogNotificationResponse.from_mongo(doc) for doc in docs]
