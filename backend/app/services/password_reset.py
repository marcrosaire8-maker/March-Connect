"""Gestion OTP pour la réinitialisation de mot de passe."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import (
    create_password_reset_token,
    decode_password_reset_token,
    generate_otp,
    hash_otp,
    hash_password,
    validate_password_strength,
    verify_otp,
)
from app.db.config import settings
from app.services.transactional_email import send_password_reset_otp_email

logger = logging.getLogger(__name__)


async def request_password_reset_otp(db: AsyncIOMotorDatabase, email: str) -> None:
    user = await db.utilisateurs.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun compte n'est associé à cette adresse email",
        )

    otp = generate_otp()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.password_reset_otp_expire_minutes)

    await db.password_reset_otps.update_one(
        {"email": email},
        {
            "$set": {
                "otp_hash": hash_otp(otp),
                "created_at": now,
                "expires_at": expires_at,
                "last_sent_at": now,
                "user_id": user["_id"],
            }
        },
        upsert=True,
    )

    try:
        send_password_reset_otp_email(email, otp)
    except Exception as exc:
        await db.password_reset_otps.delete_one({"email": email})
        logger.error("Échec envoi OTP réinitialisation à %s : %s", email, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Impossible d'envoyer l'email pour le moment. "
                "Réessayez dans quelques minutes."
            ),
        ) from exc


async def resend_password_reset_otp(db: AsyncIOMotorDatabase, email: str) -> None:
    doc = await db.password_reset_otps.find_one({"email": email})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune demande de réinitialisation en cours pour cet email",
        )

    now = datetime.now(timezone.utc)
    last_sent = doc.get("last_sent_at", now)
    elapsed = (now - last_sent).total_seconds()
    cooldown = settings.password_reset_resend_cooldown_seconds
    if elapsed < cooldown:
        remaining = int(cooldown - elapsed) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Veuillez attendre {remaining} seconde(s) avant de renvoyer le code",
        )

    user = await db.utilisateurs.find_one({"email": email})
    if not user:
        await db.password_reset_otps.delete_one({"email": email})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun compte n'est associé à cette adresse email",
        )

    otp = generate_otp()
    expires_at = now + timedelta(minutes=settings.password_reset_otp_expire_minutes)
    await db.password_reset_otps.update_one(
        {"email": email},
        {
            "$set": {
                "otp_hash": hash_otp(otp),
                "expires_at": expires_at,
                "last_sent_at": now,
            }
        },
    )

    try:
        send_password_reset_otp_email(email, otp)
    except Exception as exc:
        logger.error("Échec renvoi OTP réinitialisation à %s : %s", email, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Impossible d'envoyer l'email pour le moment. "
                "Réessayez dans quelques minutes."
            ),
        ) from exc


async def verify_password_reset_otp(
    db: AsyncIOMotorDatabase, email: str, code: str
) -> str:
    doc = await db.password_reset_otps.find_one({"email": email})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucune demande de réinitialisation en cours. Veuillez recommencer.",
        )

    now = datetime.now(timezone.utc)
    if doc["expires_at"] < now:
        await db.password_reset_otps.delete_one({"email": email})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le code a expiré. Veuillez demander un nouveau code.",
        )

    if not verify_otp(code.strip(), doc["otp_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code incorrect. Vérifiez le code reçu par email.",
        )

    await db.password_reset_otps.delete_one({"email": email})
    return create_password_reset_token(str(doc["user_id"]), email)


async def reset_password_with_token(
    db: AsyncIOMotorDatabase,
    token: str,
    password: str,
    confirm_password: str,
) -> None:
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Les mots de passe ne correspondent pas",
        )

    strength_error = validate_password_strength(password)
    if strength_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=strength_error,
        )

    try:
        payload = decode_password_reset_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La session de réinitialisation a expiré. Veuillez recommencer.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session de réinitialisation invalide. Veuillez recommencer.",
        ) from exc

    user_id = ObjectId(payload["sub"])
    result = await db.utilisateurs.update_one(
        {"_id": user_id},
        {
            "$set": {
                "mot_de_passe_hash": hash_password(password),
                "must_change_password": False,
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )
