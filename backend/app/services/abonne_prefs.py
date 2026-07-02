"""Lecture et liaison des préférences secteurs / pays d'un utilisateur."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


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


def _unique_pays(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _abonne_rank(doc: dict[str, Any]) -> int:
    score = 0
    secteurs = doc.get("secteurs_suivis") or []
    pays = doc.get("pays_suivis") or []
    if secteurs:
        score += 50 + len(secteurs)
    if pays:
        score += 50 + len(pays)
    if doc.get("preferences_configurees"):
        score += 25
    return score


async def _find_abonne_candidates(
    db: AsyncIOMotorDatabase,
    utilisateur_id: ObjectId,
    email: str,
) -> list[dict[str, Any]]:
    normalized = email.lower()
    uid_str = str(utilisateur_id)
    return await db.abonnes.find(
        {
            "$or": [
                {"utilisateur_id": utilisateur_id},
                {"utilisateur_id": uid_str},
                {"email": normalized},
            ]
        }
    ).to_list(length=20)


def _abonne_authority_key(doc: dict[str, Any]) -> tuple[int, float]:
    rank = _abonne_rank(doc)
    date_maj = doc.get("date_maj") or doc.get("date_inscription")
    ts = 0.0
    if date_maj is not None:
        if date_maj.tzinfo is None:
            date_maj = date_maj.replace(tzinfo=timezone.utc)
        ts = date_maj.timestamp()
    return rank, ts


async def consolidate_user_abonne(
    db: AsyncIOMotorDatabase,
    utilisateur_id: ObjectId,
    email: str,
) -> dict[str, Any] | None:
    """Fusionne les doublons en conservant le profil le plus récent et complet."""
    docs = await _find_abonne_candidates(db, utilisateur_id, email)
    if not docs:
        return None
    if len(docs) == 1:
        doc = docs[0]
        secteurs = _normalize_oid_list(doc.get("secteurs_suivis") or [])
        pays = _unique_pays(list(doc.get("pays_suivis") or []))
        preferences_configurees = bool(
            doc.get("preferences_configurees")
        ) or bool(secteurs and pays)
        await db.abonnes.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "email": email.lower(),
                    "utilisateur_id": utilisateur_id,
                    "secteurs_suivis": secteurs,
                    "pays_suivis": pays,
                    "preferences_configurees": preferences_configurees,
                    "actif": True,
                }
            },
        )
        merged = await db.abonnes.find_one({"_id": doc["_id"]})
        return merged

    best = max(docs, key=_abonne_authority_key)
    secteurs = _normalize_oid_list(best.get("secteurs_suivis") or [])
    pays = _unique_pays(list(best.get("pays_suivis") or []))
    preferences_configurees = bool(
        best.get("preferences_configurees")
    ) or bool(secteurs and pays)

    await db.abonnes.update_one(
        {"_id": best["_id"]},
        {
            "$set": {
                "email": email.lower(),
                "utilisateur_id": utilisateur_id,
                "secteurs_suivis": secteurs,
                "pays_suivis": pays,
                "preferences_configurees": preferences_configurees,
                "actif": True,
            }
        },
    )

    for doc in docs:
        if doc["_id"] != best["_id"]:
            await db.abonnes.delete_one({"_id": doc["_id"]})

    merged = await db.abonnes.find_one({"_id": best["_id"]})
    return merged


async def get_abonne_for_user(
    db: AsyncIOMotorDatabase,
    utilisateur_id: ObjectId,
    email: str,
) -> dict[str, Any] | None:
    """Retrouve le profil d'abonné lié au compte (id ou email)."""
    return await consolidate_user_abonne(db, utilisateur_id, email)


def abonne_preference_lists(abonne: dict[str, Any] | None) -> tuple[list[ObjectId], list[str]]:
    if not abonne:
        return [], []
    secteurs = _normalize_oid_list(abonne.get("secteurs_suivis") or [])
    pays = _unique_pays(list(abonne.get("pays_suivis") or []))
    return secteurs, pays


def abonne_has_active_preferences(abonne: dict[str, Any] | None) -> bool:
    secteurs, pays = abonne_preference_lists(abonne)
    return bool(secteurs and pays)


def abonne_keyword_list(abonne: dict[str, Any] | None) -> list[str]:
    if not abonne:
        return []
    keywords: list[str] = []
    for raw in abonne.get("mots_cles_alertes") or []:
        value = str(raw).strip().lower()
        if value and value not in keywords:
            keywords.append(value)
    return keywords


def offre_matches_keywords(offre: dict[str, Any], abonne: dict[str, Any] | None) -> bool:
    keywords = abonne_keyword_list(abonne)
    if not keywords:
        return True
    haystack = " ".join(
        [
            str(offre.get("titre") or ""),
            str(offre.get("organisme") or ""),
            str(offre.get("description") or ""),
        ]
    ).lower()
    return any(keyword in haystack for keyword in keywords)


async def ensure_abonne_linked_to_user(
    db: AsyncIOMotorDatabase,
    utilisateur_id: ObjectId,
    email: str,
) -> None:
    """Assure le lien compte ↔ abonné sans effacer les préférences existantes."""
    normalized = email.lower()
    doc = await consolidate_user_abonne(db, utilisateur_id, normalized)
    if doc:
        secteurs, pays = abonne_preference_lists(doc)
        updates: dict[str, Any] = {
            "email": normalized,
            "utilisateur_id": utilisateur_id,
            "actif": True,
            "secteurs_suivis": secteurs,
            "pays_suivis": pays,
        }
        if abonne_has_active_preferences(doc):
            updates["preferences_configurees"] = True
        await db.abonnes.update_one({"_id": doc["_id"]}, {"$set": updates})
        return

    await db.abonnes.insert_one(
        {
            "email": normalized,
            "utilisateur_id": utilisateur_id,
            "secteurs_suivis": [],
            "pays_suivis": [],
            "emails_supplementaires": [],
            "preferences_configurees": False,
            "actif": True,
            "date_inscription": datetime.now(timezone.utc),
        }
    )
