from fastapi import APIRouter, HTTPException

from app.api.deps import AdminUserDep, CurrentUserDep, DbDep
from app.api.schemas import NotificationPreviewResponse, NotificationTriggerResponse
from app.models.enums import NotificationStatus
from app.services.abonne_prefs import (
    abonne_has_active_preferences,
    get_abonne_for_user,
)
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "/trigger",
    response_model=NotificationTriggerResponse,
    summary="Déclencher manuellement l'envoi des notifications (admin)",
    description=(
        "Envoie les alertes aux abonnés actifs : offres encore ouvertes (date limite "
        "non dépassée), filtrées selon leurs préférences secteurs/pays."
    ),
)
async def trigger_notifications(_admin: AdminUserDep) -> NotificationTriggerResponse:
    result = NotificationService().run()
    return NotificationTriggerResponse(
        statut=NotificationStatus(result["statut"]),
        nb_emails_envoyes=result["nb_emails_envoyes"],
        nb_echecs=result["nb_echecs"],
        nb_offres_recentes=result["nb_offres_recentes"],
        message_erreur=result.get("message_erreur"),
    )


@router.post(
    "/preview-me",
    response_model=NotificationPreviewResponse,
    summary="Recevoir un aperçu de ses alertes email",
    description=(
        "Envoie à votre adresse un email de test contenant les offres actuellement "
        "visibles selon vos secteurs et pays (Mon compte)."
    ),
)
async def preview_my_notifications(
    user: CurrentUserDep,
    db: DbDep,
) -> NotificationPreviewResponse:
    abonne = await get_abonne_for_user(db, user.id, user.email)
    if not abonne_has_active_preferences(abonne):
        raise HTTPException(
            status_code=400,
            detail="Configurez vos secteurs et pays dans Mon compte avant l'aperçu.",
        )

    service = NotificationService()
    try:
        result = service.send_to_abonne(abonne, preview=True)
    finally:
        service.close()

    return NotificationPreviewResponse(
        statut=NotificationStatus(result["statut"]),
        nb_emails_envoyes=result["nb_emails_envoyes"],
        nb_offres=result["nb_offres"],
        message_erreur=result.get("message_erreur"),
    )
