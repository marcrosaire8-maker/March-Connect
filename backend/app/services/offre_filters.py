"""Filtres MongoDB partagés pour les offres affichées aux utilisateurs."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def active_deadline_filter(
    minimum: datetime | None = None,
    *,
    include_without_deadline: bool = True,
) -> dict[str, Any]:
    """Exclut les offres dont la date limite est dépassée."""
    now = datetime.now(timezone.utc)
    threshold = now if minimum is None else max(_as_utc(minimum), now)

    if include_without_deadline:
        return {
            "$or": [
                {"date_limite": {"$gte": threshold}},
                {"date_limite": None},
            ]
        }
    return {"date_limite": {"$gte": threshold}}


def merge_mongo_filters(*parts: dict[str, Any]) -> dict[str, Any]:
    clauses = [p for p in parts if p]
    if not clauses:
        return {}
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _normalize_oid(value: Any) -> ObjectId | None:
    if isinstance(value, ObjectId):
        return value
    if value is None:
        return None
    text = str(value)
    if ObjectId.is_valid(text):
        return ObjectId(text)
    return None


def _normalize_oid_list(values: list[Any]) -> list[ObjectId]:
    ids: list[ObjectId] = []
    seen: set[str] = set()
    for value in values:
        oid = _normalize_oid(value)
        if oid is None:
            continue
        key = str(oid)
        if key in seen:
            continue
        seen.add(key)
        ids.append(oid)
    return ids


def _oid_in(candidate: ObjectId, collection: list[ObjectId]) -> bool:
    key = str(candidate)
    return any(str(item) == key for item in collection)


def user_preferences_filter(
    secteurs_suivis: list[Any],
    pays_suivis: list[str],
    *,
    secteur_id: Any | None = None,
    pays: str | None = None,
) -> dict[str, Any]:
    """Restreint la liste aux secteurs et pays choisis dans Mon compte (secteur strict)."""
    parts: list[dict[str, Any]] = []
    ids = _normalize_oid_list(secteurs_suivis)
    allowed_pays = [p for p in pays_suivis if p]

    if ids:
        parsed_sector = _normalize_oid(secteur_id)
        if parsed_sector is not None:
            parts.append(
                {"secteur_id": parsed_sector}
                if _oid_in(parsed_sector, ids)
                else {"secteur_id": {"$in": []}}
            )
        else:
            parts.append({"secteur_id": {"$in": ids}})

    if allowed_pays:
        if pays:
            parts.append(
                {"pays": pays} if pays in allowed_pays else {"pays": {"$in": []}}
            )
        else:
            parts.append({"pays": {"$in": allowed_pays}})

    return merge_mongo_filters(*parts)


def text_search_filter(query: str | None) -> dict[str, Any]:
    """Recherche insensible à la casse sur titre, organisme et description."""
    if not query or not query.strip():
        return {}
    pattern = {"$regex": re.escape(query.strip()), "$options": "i"}
    return {
        "$or": [
            {"titre": pattern},
            {"organisme": pattern},
            {"description": pattern},
        ]
    }


def favoris_filter(offre_ids: list[ObjectId]) -> dict[str, Any]:
    if not offre_ids:
        return {"_id": {"$in": []}}
    return {"_id": {"$in": offre_ids}}


def mes_sites_filter(source_ids: list[ObjectId]) -> dict[str, Any]:
    if not source_ids:
        return {"source_id": {"$in": []}}
    return {"source_id": {"$in": source_ids}}


def offres_list_aggregation_pipeline(
    query: dict[str, Any],
    *,
    skip: int = 0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Tri : offres avec date limite d'abord, sans date limite en dernier."""
    pipeline: list[dict[str, Any]] = [
        {"$match": query},
        {
            "$addFields": {
                "_sans_date_limite": {
                    "$cond": [
                        {"$eq": [{"$type": "$date_limite"}, "date"]},
                        0,
                        1,
                    ]
                }
            }
        },
        {
            "$sort": {
                "_sans_date_limite": 1,
                "date_limite": 1,
                "date_scraping": -1,
                "date_publication": -1,
                "_id": -1,
            }
        },
    ]
    if skip:
        pipeline.append({"$skip": skip})
    if limit is not None:
        pipeline.append({"$limit": limit})
    pipeline.append({"$unset": "_sans_date_limite"})
    return pipeline


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
