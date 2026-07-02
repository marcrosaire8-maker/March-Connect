import hashlib
import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.db.config import settings
from app.models.enums import UserRole

ALGORITHM = "HS256"
PASSWORD_SPECIAL_CHARS = r"!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: str,
    email: str,
    role: UserRole,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "role": role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_otp(length: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def hash_otp(otp: str) -> str:
    payload = f"{otp}:{settings.jwt_secret}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_otp(otp: str, otp_hash: str) -> bool:
    return secrets.compare_digest(hash_otp(otp), otp_hash)


def validate_password_strength(password: str) -> str | None:
    if len(password) < 8:
        return "Le mot de passe doit contenir au moins 8 caractères"
    if not re.search(r"[A-Z]", password):
        return "Le mot de passe doit contenir au moins une lettre majuscule"
    if not re.search(r"[a-z]", password):
        return "Le mot de passe doit contenir au moins une lettre minuscule"
    if not re.search(r"\d", password):
        return "Le mot de passe doit contenir au moins un chiffre"
    if not re.search(rf"[{re.escape(PASSWORD_SPECIAL_CHARS)}]", password):
        return "Le mot de passe doit contenir au moins un caractère spécial"
    return None


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    if payload.get("type") == "password_reset":
        raise jwt.InvalidTokenError("Token de réinitialisation utilisé comme jeton de session")
    return payload


def create_password_reset_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "type": "password_reset",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_password_reset_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    if payload.get("type") != "password_reset":
        raise jwt.InvalidTokenError("Type de jeton invalide")
    return payload


def create_google_link_token(
    google_id: str,
    email: str,
    *,
    prenom: str | None = None,
    nom: str | None = None,
    photo_profil: str | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload: dict[str, Any] = {
        "sub": google_id,
        "email": email,
        "type": "google_link",
        "exp": expire,
    }
    if prenom:
        payload["prenom"] = prenom
    if nom:
        payload["nom"] = nom
    if photo_profil:
        payload["photo_profil"] = photo_profil
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_google_link_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    if payload.get("type") != "google_link":
        raise jwt.InvalidTokenError("Type de jeton invalide")
    return payload


def create_apple_link_token(
    apple_id: str,
    email: str,
    *,
    prenom: str | None = None,
    nom: str | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload: dict[str, Any] = {
        "sub": apple_id,
        "email": email,
        "type": "apple_link",
        "exp": expire,
    }
    if prenom:
        payload["prenom"] = prenom
    if nom:
        payload["nom"] = nom
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_apple_link_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    if payload.get("type") != "apple_link":
        raise jwt.InvalidTokenError("Type de jeton invalide")
    return payload
