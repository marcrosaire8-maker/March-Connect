"""Authentification Apple (Sign in with Apple)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import jwt
from fastapi import status
from jwt import PyJWKClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import (
    create_access_token,
    create_apple_link_token,
    decode_apple_link_token,
    verify_password,
)
from app.db.config import settings
from app.models.enums import AuthProvider, EmailVerificationStatus, UserRole
from app.services.abonne_prefs import ensure_abonne_linked_to_user
from app.services.transactional_email import deliver_welcome_email_if_needed

logger = logging.getLogger(__name__)

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"


class AppleAuthError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@lru_cache(maxsize=1)
def _get_apple_jwk_client() -> PyJWKClient:
    return PyJWKClient(APPLE_JWKS_URL, cache_keys=True)


def _normalize_apple_email(email: str) -> str:
    """Conserve l'adresse telle qu'Apple la fournit (y compris le relais privé)."""
    return email.strip().lower()


def _email_verified(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1"}


def verify_apple_credential(credential: str) -> dict[str, Any]:
    if not settings.apple_client_id:
        raise AppleAuthError(
            "La connexion Apple n'est pas configurée sur le serveur",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        signing_key = _get_apple_jwk_client().get_signing_key_from_jwt(credential)
        payload = jwt.decode(
            credential,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.apple_client_id,
            issuer=APPLE_ISSUER,
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppleAuthError(
            "La session Apple a expiré. Veuillez réessayer.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc
    except jwt.PyJWTError as exc:
        logger.warning("Jeton Apple rejeté : %s", exc)
        raise AppleAuthError(
            "Authentification Apple invalide. Veuillez réessayer.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc

    apple_id = payload.get("sub")
    if not apple_id:
        raise AppleAuthError(
            "Informations Apple incomplètes",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    email = payload.get("email")
    normalized_email = _normalize_apple_email(email) if email else None
    if email and not _email_verified(payload.get("email_verified", True)):
        raise AppleAuthError(
            "L'adresse email Apple n'est pas vérifiée",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    is_private_email = _email_verified(payload.get("is_private_email", False))

    return {
        "apple_id": apple_id,
        "email": normalized_email,
        "is_private_email": is_private_email,
    }


def _profile_updates(
    profile: dict[str, Any],
    *,
    prenom: str | None = None,
    nom: str | None = None,
) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if prenom:
        updates["prenom"] = prenom.strip()
    if nom:
        updates["nom"] = nom.strip()
    for field in ("prenom", "nom"):
        value = profile.get(field)
        if value and field not in updates:
            updates[field] = value
    return updates


def _resolve_auth_provider(user: dict[str, Any]) -> str:
    has_password = bool(user.get("mot_de_passe_hash"))
    has_google = bool(user.get("google_id"))
    has_apple = bool(user.get("apple_id"))
    if has_password and (has_google or has_apple):
        return AuthProvider.BOTH.value
    if has_apple:
        return AuthProvider.APPLE.value
    if has_google:
        return AuthProvider.GOOGLE.value
    return AuthProvider.EMAIL.value


async def _issue_session(db: AsyncIOMotorDatabase, user: dict[str, Any]) -> str:
    await ensure_abonne_linked_to_user(db, user["_id"], user["email"])
    await deliver_welcome_email_if_needed(
        db,
        user_id=user["_id"],
        email=user["email"],
    )
    return create_access_token(
        str(user["_id"]),
        user["email"],
        UserRole(user["role"]),
    )


async def authenticate_with_apple(
    db: AsyncIOMotorDatabase,
    credential: str,
    *,
    prenom: str | None = None,
    nom: str | None = None,
) -> dict[str, Any]:
    profile = verify_apple_credential(credential)
    apple_id = profile["apple_id"]
    email = profile.get("email")

    user_by_apple = await db.utilisateurs.find_one({"apple_id": apple_id})
    if user_by_apple:
        updates = _profile_updates(profile, prenom=prenom, nom=nom)
        for field in ("prenom", "nom"):
            if updates.get(field) and user_by_apple.get(field):
                updates.pop(field, None)
        if updates:
            await db.utilisateurs.update_one({"_id": user_by_apple["_id"]}, {"$set": updates})
            user_by_apple.update(updates)
        token = await _issue_session(db, user_by_apple)
        return {"status": "authenticated", "access_token": token}

    if not email:
        raise AppleAuthError(
            "Impossible de créer le compte : Apple n'a pas fourni d'adresse email. "
            "Réessayez et autorisez le partage de votre email.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user_by_email = await db.utilisateurs.find_one({"email": email})
    if user_by_email:
        if user_by_email.get("apple_id"):
            updates = _profile_updates(profile, prenom=prenom, nom=nom)
            for field in ("prenom", "nom"):
                if updates.get(field) and user_by_email.get(field):
                    updates.pop(field, None)
            if updates:
                await db.utilisateurs.update_one(
                    {"_id": user_by_email["_id"]}, {"$set": updates}
                )
                user_by_email.update(updates)
            token = await _issue_session(db, user_by_email)
            return {"status": "authenticated", "access_token": token}

        link_token = create_apple_link_token(
            apple_id,
            email,
            prenom=prenom or profile.get("prenom"),
            nom=nom or profile.get("nom"),
        )
        return {
            "status": "link_required",
            "link_token": link_token,
            "email": email,
            "message": (
                "Un compte existe déjà avec cette adresse email. "
                "Confirmez votre mot de passe pour associer Apple."
            ),
        }

    now = datetime.now(timezone.utc)
    name_updates = _profile_updates(profile, prenom=prenom, nom=nom)
    doc: dict[str, Any] = {
        "email": email,
        "apple_id": apple_id,
        "role": UserRole.CLIENT.value,
        "auth_provider": AuthProvider.APPLE.value,
        "email_verifie": True,
        "statut_email": EmailVerificationStatus.VERIFIE.value,
        "date_verification_email": now,
        "date_inscription": now,
        "must_change_password": False,
        **name_updates,
    }
    if profile.get("is_private_email"):
        doc["apple_private_email"] = True

    result = await db.utilisateurs.insert_one(doc)
    doc["_id"] = result.inserted_id
    token = await _issue_session(db, doc)
    return {"status": "authenticated", "access_token": token}


async def link_apple_account(
    db: AsyncIOMotorDatabase, link_token: str, password: str
) -> str:
    try:
        payload = decode_apple_link_token(link_token)
    except jwt.ExpiredSignatureError as exc:
        raise AppleAuthError(
            "La demande d'association a expiré. Recommencez avec Apple.",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise AppleAuthError(
            "Demande d'association invalide. Recommencez avec Apple.",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    email = _normalize_apple_email(payload["email"])
    apple_id = payload["sub"]
    user = await db.utilisateurs.find_one({"email": email})
    if not user:
        raise AppleAuthError(
            "Aucun compte trouvé pour cette adresse email",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if user.get("apple_id") == apple_id:
        return await _issue_session(db, user)

    password_hash = user.get("mot_de_passe_hash")
    if not password_hash or not verify_password(password, password_hash):
        raise AppleAuthError(
            "Mot de passe incorrect",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    existing_apple = await db.utilisateurs.find_one(
        {"apple_id": apple_id, "_id": {"$ne": user["_id"]}}
    )
    if existing_apple:
        raise AppleAuthError(
            "Ce compte Apple est déjà associé à un autre utilisateur",
            status_code=status.HTTP_409_CONFLICT,
        )

    updates: dict[str, Any] = {
        "apple_id": apple_id,
        "email_verifie": True,
        "statut_email": EmailVerificationStatus.VERIFIE.value,
    }
    if not user.get("date_verification_email"):
        updates["date_verification_email"] = datetime.now(timezone.utc)
    for field in ("prenom", "nom"):
        if payload.get(field) and not user.get(field):
            updates[field] = payload[field]

    user_with_apple = {**user, **updates}
    updates["auth_provider"] = _resolve_auth_provider(user_with_apple)

    await db.utilisateurs.update_one({"_id": user["_id"]}, {"$set": updates})
    user.update(updates)
    return await _issue_session(db, user)


def get_apple_redirect_uri() -> str:
    return settings.frontend_url.rstrip("/")
