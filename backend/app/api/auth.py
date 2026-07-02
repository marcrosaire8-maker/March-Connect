import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response, status
from pymongo.errors import DuplicateKeyError

from app.api.deps import CurrentUserDep, DbDep
from app.api.schemas import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    AppleAuthRequest,
    AppleAuthResponse,
    AppleConfigResponse,
    AppleLinkRequest,
    GoogleAuthRequest,
    GoogleAuthResponse,
    GoogleConfigResponse,
    GoogleLinkRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    ResendEmailVerificationRequest,
    ResendResetOtpRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailOtpRequest,
    VerifyResetOtpRequest,
    VerifyResetOtpResponse,
)
from app.core.security import (
    create_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.db.config import settings
from app.models.enums import AuthProvider, EmailVerificationStatus, UserRole
from app.services.abonne_prefs import (
    abonne_has_active_preferences,
    ensure_abonne_linked_to_user,
    get_abonne_for_user,
)
from app.services.apple_auth import (
    AppleAuthError,
    authenticate_with_apple,
    get_apple_redirect_uri,
    link_apple_account,
)
from app.services.google_auth import (
    GoogleAuthError,
    authenticate_with_google,
    link_google_account,
)
from app.services.email_verification import (
    ensure_login_email_verified,
    resend_email_verification_otp,
    send_email_verification_otp,
    verify_email_otp,
)
from app.services.password_reset import (
    request_password_reset_otp,
    resend_password_reset_otp,
    reset_password_with_token,
    verify_password_reset_otp,
)
from app.services.transactional_email import send_welcome_email_safe
from app.services.user_cleanup import delete_user_and_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

FORGOT_PASSWORD_SENT_MESSAGE = (
    "Un code de vérification a été envoyé à votre adresse email. "
    "Consultez votre boîte mail."
)
PASSWORD_RESET_SUCCESS_MESSAGE = (
    "Votre mot de passe a été modifié avec succès. Vous pouvez vous connecter."
)
EMAIL_VERIFICATION_SENT_MESSAGE = (
    "Un code de vérification a été envoyé à votre adresse email. "
    "Consultez votre boîte mail pour activer votre compte."
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte client",
)
async def register(payload: RegisterRequest, db: DbDep) -> RegisterResponse:
    email = str(payload.email).lower()
    now = datetime.now(timezone.utc)
    doc: dict = {
        "email": email,
        "mot_de_passe_hash": hash_password(payload.password),
        "role": UserRole.CLIENT.value,
        "auth_provider": AuthProvider.EMAIL.value,
        "email_verifie": False,
        "statut_email": EmailVerificationStatus.EN_ATTENTE.value,
        "date_inscription": now,
        "must_change_password": False,
    }
    if payload.prenom:
        doc["prenom"] = payload.prenom.strip()
    if payload.nom:
        doc["nom"] = payload.nom.strip()
    try:
        result = await db.utilisateurs.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email",
        ) from None

    await ensure_abonne_linked_to_user(db, result.inserted_id, email)
    await send_email_verification_otp(db, email)

    return RegisterResponse(
        status="verification_required",
        email=email,
        message=EMAIL_VERIFICATION_SENT_MESSAGE,
    )


@router.post("/login", response_model=TokenResponse, summary="Connexion")
async def login(payload: LoginRequest, db: DbDep) -> TokenResponse:
    email = str(payload.email).strip().lower()
    user = await db.utilisateurs.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    if not user.get("mot_de_passe_hash"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Ce compte utilise une connexion sociale (Google ou Apple). "
                "Utilisez le bouton correspondant."
            ),
        )
    if not verify_password(payload.password, user["mot_de_passe_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    ensure_login_email_verified(user)

    await ensure_abonne_linked_to_user(db, user["_id"], email)

    token = create_access_token(
        str(user["_id"]),
        user["email"],
        UserRole(user["role"]),
    )
    return TokenResponse(access_token=token)


@router.get(
    "/google/config",
    response_model=GoogleConfigResponse,
    summary="Configuration publique Google Sign-In",
)
async def google_config() -> GoogleConfigResponse:
    client_id = settings.google_client_id.strip()
    return GoogleConfigResponse(
        enabled=bool(client_id),
        client_id=client_id or None,
    )


@router.post(
    "/google",
    response_model=GoogleAuthResponse,
    summary="Connexion ou inscription avec Google",
)
async def google_auth(payload: GoogleAuthRequest, db: DbDep) -> GoogleAuthResponse:
    try:
        result = await authenticate_with_google(db, payload.credential)
    except GoogleAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Erreur authentification Google : %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Erreur lors de l'authentification Google. Réessayez ultérieurement.",
        ) from exc

    return GoogleAuthResponse(**result)


@router.post(
    "/google/link",
    response_model=TokenResponse,
    summary="Associer un compte Google à un compte existant",
)
async def google_link(payload: GoogleLinkRequest, db: DbDep) -> TokenResponse:
    try:
        access_token = await link_google_account(db, payload.link_token, payload.password)
    except GoogleAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Erreur association Google : %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible d'associer le compte Google. Réessayez ultérieurement.",
        ) from exc
    return TokenResponse(access_token=access_token)


@router.get(
    "/apple/config",
    response_model=AppleConfigResponse,
    summary="Configuration publique Sign in with Apple",
)
async def apple_config() -> AppleConfigResponse:
    client_id = settings.apple_client_id.strip()
    return AppleConfigResponse(
        enabled=bool(client_id),
        client_id=client_id or None,
        redirect_uri=get_apple_redirect_uri() if client_id else None,
    )


@router.post(
    "/apple",
    response_model=AppleAuthResponse,
    summary="Connexion ou inscription avec Apple",
)
async def apple_auth(payload: AppleAuthRequest, db: DbDep) -> AppleAuthResponse:
    try:
        result = await authenticate_with_apple(
            db,
            payload.credential,
            prenom=payload.prenom,
            nom=payload.nom,
        )
    except AppleAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Erreur authentification Apple : %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Erreur lors de l'authentification Apple. Réessayez ultérieurement.",
        ) from exc

    return AppleAuthResponse(**result)


@router.post(
    "/apple/link",
    response_model=TokenResponse,
    summary="Associer un compte Apple à un compte existant",
)
async def apple_link(payload: AppleLinkRequest, db: DbDep) -> TokenResponse:
    try:
        access_token = await link_apple_account(db, payload.link_token, payload.password)
    except AppleAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Erreur association Apple : %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible d'associer le compte Apple. Réessayez ultérieurement.",
        ) from exc
    return TokenResponse(access_token=access_token)


@router.post(
    "/verify-email-otp",
    response_model=TokenResponse,
    summary="Vérifier l'adresse email avec le code OTP",
)
async def verify_email(payload: VerifyEmailOtpRequest, db: DbDep) -> TokenResponse:
    email = str(payload.email).lower()
    access_token = await verify_email_otp(db, email, payload.code)
    send_welcome_email_safe(email)
    return TokenResponse(access_token=access_token)


@router.post(
    "/resend-email-verification",
    response_model=ForgotPasswordResponse,
    summary="Renvoyer le code de vérification email",
)
async def resend_email_verification(
    payload: ResendEmailVerificationRequest, db: DbDep
) -> ForgotPasswordResponse:
    email = str(payload.email).lower()
    await resend_email_verification_otp(db, email)
    return ForgotPasswordResponse(message=EMAIL_VERIFICATION_SENT_MESSAGE)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Recevoir un code OTP par email",
)
async def forgot_password(payload: ForgotPasswordRequest, db: DbDep) -> ForgotPasswordResponse:
    email = str(payload.email).lower()
    await request_password_reset_otp(db, email)
    return ForgotPasswordResponse(message=FORGOT_PASSWORD_SENT_MESSAGE)


@router.post(
    "/verify-reset-otp",
    response_model=VerifyResetOtpResponse,
    summary="Vérifier le code OTP de réinitialisation",
)
async def verify_reset_otp(
    payload: VerifyResetOtpRequest, db: DbDep
) -> VerifyResetOtpResponse:
    email = str(payload.email).lower()
    reset_token = await verify_password_reset_otp(db, email, payload.code)
    return VerifyResetOtpResponse(reset_token=reset_token)


@router.post(
    "/resend-reset-otp",
    response_model=ForgotPasswordResponse,
    summary="Renvoyer le code OTP de réinitialisation",
)
async def resend_reset_otp(
    payload: ResendResetOtpRequest, db: DbDep
) -> ForgotPasswordResponse:
    email = str(payload.email).lower()
    await resend_password_reset_otp(db, email)
    return ForgotPasswordResponse(message=FORGOT_PASSWORD_SENT_MESSAGE)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Définir un nouveau mot de passe après vérification OTP",
)
async def reset_password(payload: ResetPasswordRequest, db: DbDep) -> MessageResponse:
    await reset_password_with_token(
        db,
        payload.token,
        payload.password,
        payload.confirm_password,
    )
    return MessageResponse(message=PASSWORD_RESET_SUCCESS_MESSAGE)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Choisir un nouveau mot de passe après connexion avec mot de passe provisoire",
)
async def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUserDep,
    db: DbDep,
) -> MessageResponse:
    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=422,
            detail="Les mots de passe ne correspondent pas",
        )

    strength_error = validate_password_strength(payload.new_password)
    if strength_error:
        raise HTTPException(status_code=422, detail=strength_error)

    doc = await db.utilisateurs.find_one({"_id": user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if not doc.get("must_change_password"):
        raise HTTPException(
            status_code=400,
            detail="Aucun changement de mot de passe requis",
        )

    await db.utilisateurs.update_one(
        {"_id": user.id},
        {
            "$set": {
                "mot_de_passe_hash": hash_password(payload.new_password),
                "must_change_password": False,
            }
        },
    )
    return MessageResponse(message="Mot de passe mis à jour.")


@router.get("/me", response_model=UserResponse, summary="Profil de l'utilisateur connecté")
async def me(user: CurrentUserDep, db: DbDep) -> UserResponse:
    doc = await db.utilisateurs.find_one({"_id": user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    abonne = await get_abonne_for_user(db, user.id, user.email)
    preferences_configurees = False
    if abonne:
        preferences_configurees = abonne_has_active_preferences(abonne)
    elif user.is_admin:
        preferences_configurees = True
    return UserResponse.from_mongo(
        doc,
        preferences_configurees=preferences_configurees,
    )


@router.delete(
    "/me",
    status_code=204,
    summary="Supprimer son compte et toutes ses données",
)
async def delete_my_account(
    payload: DeleteAccountRequest,
    user: CurrentUserDep,
    db: DbDep,
) -> Response:
    doc = await db.utilisateurs.find_one({"_id": user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    password_hash = doc.get("mot_de_passe_hash")
    if password_hash:
        if not verify_password(payload.password, password_hash):
            raise HTTPException(status_code=401, detail="Mot de passe incorrect")

    if user.is_admin:
        admin_count = await db.utilisateurs.count_documents({"role": UserRole.ADMIN.value})
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Impossible de supprimer le dernier compte administrateur",
            )

    deleted = await delete_user_and_data(db, user.id, user.email)
    if not deleted:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return Response(status_code=204)
