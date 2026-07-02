from bson import ObjectId
from fastapi import APIRouter, HTTPException, Response

from app.api.deps import AdminUserDep, DbDep
from app.api.schemas import AdminUtilisateurResponse
from app.models.enums import UserRole
from app.services.user_cleanup import delete_user_and_data

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/utilisateurs",
    response_model=list[AdminUtilisateurResponse],
    summary="Liste des utilisateurs (admin)",
)
async def list_utilisateurs(
    db: DbDep,
    _admin: AdminUserDep,
) -> list[AdminUtilisateurResponse]:
    users = await db.utilisateurs.find().sort("date_inscription", -1).to_list(length=None)
    return [
        AdminUtilisateurResponse(
            id=str(user["_id"]),
            email=user["email"],
            role=UserRole(user["role"]),
            date_inscription=user["date_inscription"],
        )
        for user in users
    ]


@router.delete(
    "/utilisateurs/{user_id}",
    status_code=204,
    summary="Supprimer un utilisateur et toutes ses données (admin)",
)
async def delete_utilisateur(
    user_id: str,
    db: DbDep,
    admin: AdminUserDep,
) -> Response:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Identifiant invalide")

    target_id = ObjectId(user_id)
    if target_id == admin.id:
        raise HTTPException(
            status_code=400,
            detail="Vous ne pouvez pas supprimer votre propre compte depuis l'administration",
        )

    target = await db.utilisateurs.find_one({"_id": target_id})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if target.get("role") == UserRole.ADMIN.value:
        admin_count = await db.utilisateurs.count_documents({"role": UserRole.ADMIN.value})
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Impossible de supprimer le dernier compte administrateur",
            )

    deleted = await delete_user_and_data(db, target_id, target["email"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return Response(status_code=204)
