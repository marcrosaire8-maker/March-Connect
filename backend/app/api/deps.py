from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Optional

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_access_token
from app.db.connection import get_database
from app.models.enums import UserRole

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIOMotorDatabase:
    return get_database()


DbDep = Annotated[AsyncIOMotorDatabase, Depends(get_db)]


@dataclass
class CurrentUser:
    id: ObjectId
    email: str
    role: UserRole

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN


async def _load_user_from_token(
    db: AsyncIOMotorDatabase,
    token: str | None,
) -> CurrentUser | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id or not ObjectId.is_valid(user_id):
            return None
        user = await db.utilisateurs.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        return CurrentUser(
            id=user["_id"],
            email=user["email"],
            role=UserRole(user["role"]),
        )
    except Exception:
        return None


async def get_optional_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> CurrentUser | None:
    if credentials is None:
        return None
    return await _load_user_from_token(db, credentials.credentials)


async def get_current_user(
    user: Annotated[CurrentUser | None, Depends(get_optional_user)],
) -> CurrentUser:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return user


OptionalUserDep = Annotated[Optional[CurrentUser], Depends(get_optional_user)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
AdminUserDep = Annotated[CurrentUser, Depends(get_current_admin)]
