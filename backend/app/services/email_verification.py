"""Vérification d'adresse e-mail à l'inscription (OTP)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import (
    create_access_token,
    generate_otp,
    hash_otp,
    verify_otp,
)
from app.db.config import settings
from app.models.enums import EmailVerificationStatus, UserRole
from app.services.abonne_prefs import ensure_abonne_linked_to_user
from app.services.transactional_email import send_email_verification_otp_email

logger = logging.getLogger(__name__)


def _is_email_verified(user: dict) -> bool:
    if "email_verifie" in user:
        return bool(user["email_verifie"])
    return True


async def send_email_verification_otp(db: AsyncIOMotorDatabase, email: str) -> None:
    user = await db.utilisateurs.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun compte n'est associé à cette adresse email",
        )
    if _is_email_verified(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette adresse email est déjà vérifiée",
        )

    otp = generate_otp()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.email_verification_otp_expire_minutes)

    await db.email_verification_otps.update_one(
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

    await db.utilisateurs.update_one(
        {"_id": user["_id"]},
        {"$set": {"statut_email": EmailVerificationStatus.EN_ATTENTE.value}},
    )

    try:
        send_email_verification_otp_email(email, otp)
    except Exception as exc:
        await db.email_verification_otps.delete_one({"email": email})
        logger.error("Échec envoi OTP vérification email à %s : %s", email, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Impossible d'envoyer l'email de vérification pour le moment. "
                "Réessayez dans quelques minutes."
            ),
        ) from exc


async def resend_email_verification_otp(db: AsyncIOMotorDatabase, email: str) -> None:
    user = await db.utilisateurs.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun compte n'est associé à cette adresse email",
        )
    if _is_email_verified(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette adresse email est déjà vérifiée",
        )

    doc = await db.email_verification_otps.find_one({"email": email})
    now = datetime.now(timezone.utc)
    if doc:
        last_sent = doc.get("last_sent_at", now)
        elapsed = (now - last_sent).total_seconds()
        cooldown = settings.email_verification_resend_cooldown_seconds
        if elapsed < cooldown:
            remaining = int(cooldown - elapsed) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Veuillez attendre {remaining} seconde(s) avant de renvoyer le code",
            )

    await send_email_verification_otp(db, email)


async def verify_email_otp(db: AsyncIOMotorDatabase, email: str, code: str) -> str:
    user = await db.utilisateurs.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun compte n'est associé à cette adresse email",
        )
    if _is_email_verified(user):
        return await _issue_session(db, user)

    doc = await db.email_verification_otps.find_one({"email": email})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun code de vérification en cours. Demandez un nouveau code.",
        )

    now = datetime.now(timezone.utc)
    if doc["expires_at"] < now:
        await db.email_verification_otps.delete_one({"email": email})
        await db.utilisateurs.update_one(
            {"_id": user["_id"]},
            {"$set": {"statut_email": EmailVerificationStatus.NON_VERIFIE.value}},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le code a expiré. Demandez un nouveau code de vérification.",
        )

    if not verify_otp(code.strip(), doc["otp_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code incorrect. Vérifiez le code reçu par email.",
        )

    verified_at = datetime.now(timezone.utc)
    await db.utilisateurs.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "email_verifie": True,
                "statut_email": EmailVerificationStatus.VERIFIE.value,
                "date_verification_email": verified_at,
            }
        },
    )
    await db.email_verification_otps.delete_one({"email": email})

    user["email_verifie"] = True
    user["statut_email"] = EmailVerificationStatus.VERIFIE.value
    user["date_verification_email"] = verified_at
    return await _issue_session(db, user)


async def _issue_session(db: AsyncIOMotorDatabase, user: dict) -> str:
    await ensure_abonne_linked_to_user(db, user["_id"], user["email"])
    return create_access_token(
        str(user["_id"]),
        user["email"],
        UserRole(user["role"]),
    )


def ensure_login_email_verified(user: dict) -> None:
    if not _is_email_verified(user):
        statut = user.get("statut_email", EmailVerificationStatus.NON_VERIFIE.value)
        if statut == EmailVerificationStatus.EN_ATTENTE.value:
            detail = (
                "Votre adresse email n'est pas encore vérifiée. "
                "Consultez votre boîte mail ou demandez un nouveau code."
            )
        else:
            detail = (
                "Votre adresse email n'est pas vérifiée. "
                "Vérifiez votre email pour vous connecter."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
