"""Authentification Google (Sign in with Google)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
import jwt
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import (
    create_access_token,
    create_google_link_token,
    decode_google_link_token,
    hash_password,
    verify_password,
)
from app.db.config import settings
from app.models.enums import AuthProvider, EmailVerificationStatus, UserRole
from app.services.abonne_prefs import ensure_abonne_linked_to_user
from app.services.transactional_email import send_welcome_email_safe

logger = logging.getLogger(__name__)

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleAuthError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def verify_google_credential(credential: str) -> dict[str, Any]:
    if not settings.google_client_id:
        raise GoogleAuthError(
            "La connexion Google n'est pas configurée sur le serveur",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        response = httpx.get(
            GOOGLE_TOKENINFO_URL,
            params={"id_token": credential},
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        logger.error("Erreur réseau vérification Google : %s", exc)
        raise GoogleAuthError(
            "Impossible de vérifier le compte Google. Réessayez ultérieurement.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc

    if response.status_code != 200:
        logger.warning("Jeton Google rejeté (%s) : %s", response.status_code, response.text[:200])
        raise GoogleAuthError(
            "Authentification Google invalide. Veuillez réessayer.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    idinfo = response.json()
    audience = idinfo.get("aud") or idinfo.get("azp")
    if audience != settings.google_client_id:
        raise GoogleAuthError(
            "Jeton Google émis pour une autre application",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if idinfo.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise GoogleAuthError(
            "Émetteur Google invalide",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    google_id = idinfo.get("sub")
    email = (idinfo.get("email") or "").lower()
    email_verified = str(idinfo.get("email_verified", "")).lower() in {"true", "1"}
    if not google_id or not email:
        raise GoogleAuthError(
            "Informations Google incomplètes (email requis)",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not email_verified:
        raise GoogleAuthError(
            "L'adresse email Google n'est pas vérifiée",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return {
        "google_id": google_id,
        "email": email,
        "prenom": idinfo.get("given_name"),
        "nom": idinfo.get("family_name"),
        "photo_profil": idinfo.get("picture"),
    }


def _profile_updates(profile: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    for field in ("prenom", "nom", "photo_profil"):
        value = profile.get(field)
        if value:
            updates[field] = value
    return updates


async def _issue_session(db: AsyncIOMotorDatabase, user: dict[str, Any]) -> str:
    await ensure_abonne_linked_to_user(db, user["_id"], user["email"])
    return create_access_token(
        str(user["_id"]),
        user["email"],
        UserRole(user["role"]),
    )


async def authenticate_with_google(
    db: AsyncIOMotorDatabase, credential: str
) -> dict[str, Any]:
    profile = verify_google_credential(credential)
    google_id = profile["google_id"]
    email = profile["email"]

    user_by_google = await db.utilisateurs.find_one({"google_id": google_id})
    if user_by_google:
        updates = _profile_updates(profile)
        if updates:
            await db.utilisateurs.update_one({"_id": user_by_google["_id"]}, {"$set": updates})
            user_by_google.update(updates)
        token = await _issue_session(db, user_by_google)
        return {"status": "authenticated", "access_token": token}

    user_by_email = await db.utilisateurs.find_one({"email": email})
    if user_by_email:
        if user_by_email.get("google_id"):
            updates = _profile_updates(profile)
            if updates:
                await db.utilisateurs.update_one(
                    {"_id": user_by_email["_id"]}, {"$set": updates}
                )
                user_by_email.update(updates)
            token = await _issue_session(db, user_by_email)
            return {"status": "authenticated", "access_token": token}

        link_token = create_google_link_token(
            google_id,
            email,
            prenom=profile.get("prenom"),
            nom=profile.get("nom"),
            photo_profil=profile.get("photo_profil"),
        )
        return {
            "status": "link_required",
            "link_token": link_token,
            "email": email,
            "message": (
                "Un compte existe déjà avec cette adresse email. "
                "Confirmez votre mot de passe pour associer Google."
            ),
        }

    now = datetime.now(timezone.utc)
    doc: dict[str, Any] = {
        "email": email,
        "google_id": google_id,
        "prenom": profile.get("prenom"),
        "nom": profile.get("nom"),
        "photo_profil": profile.get("photo_profil"),
        "role": UserRole.CLIENT.value,
        "auth_provider": AuthProvider.GOOGLE.value,
        "email_verifie": True,
        "statut_email": EmailVerificationStatus.VERIFIE.value,
        "date_verification_email": now,
        "date_inscription": now,
        "must_change_password": False,
    }
    result = await db.utilisateurs.insert_one(doc)
    doc["_id"] = result.inserted_id
    send_welcome_email_safe(email)
    token = await _issue_session(db, doc)
    return {"status": "authenticated", "access_token": token}


async def link_google_account(
    db: AsyncIOMotorDatabase, link_token: str, password: str
) -> str:
    try:
        payload = decode_google_link_token(link_token)
    except jwt.ExpiredSignatureError as exc:
        raise GoogleAuthError(
            "La demande d'association a expiré. Recommencez avec Google.",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise GoogleAuthError(
            "Demande d'association invalide. Recommencez avec Google.",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    email = payload["email"].lower()
    google_id = payload["sub"]
    user = await db.utilisateurs.find_one({"email": email})
    if not user:
        raise GoogleAuthError(
            "Aucun compte trouvé pour cette adresse email",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if user.get("google_id") == google_id:
        return await _issue_session(db, user)

    password_hash = user.get("mot_de_passe_hash")
    if not password_hash or not verify_password(password, password_hash):
        raise GoogleAuthError(
            "Mot de passe incorrect",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    existing_google = await db.utilisateurs.find_one(
        {"google_id": google_id, "_id": {"$ne": user["_id"]}}
    )
    if existing_google:
        raise GoogleAuthError(
            "Ce compte Google est déjà associé à un autre utilisateur",
            status_code=status.HTTP_409_CONFLICT,
        )

    updates: dict[str, Any] = {
        "google_id": google_id,
        "auth_provider": AuthProvider.BOTH.value,
        "email_verifie": True,
        "statut_email": EmailVerificationStatus.VERIFIE.value,
    }
    if not user.get("date_verification_email"):
        updates["date_verification_email"] = datetime.now(timezone.utc)
    for field in ("prenom", "nom", "photo_profil"):
        if payload.get(field) and not user.get(field):
            updates[field] = payload[field]

    await db.utilisateurs.update_one({"_id": user["_id"]}, {"$set": updates})
    user.update(updates)
    return await _issue_session(db, user)
