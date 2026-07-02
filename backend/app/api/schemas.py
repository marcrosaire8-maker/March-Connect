from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

from app.models.enums import (
    NotificationStatus,
    ScrapingStatus,
    ScrapingType,
    UserRole,
)
from app.core.security import validate_password_strength


def _require_object_id(value: str, field_name: str = "id") -> str:
    if not ObjectId.is_valid(value):
        raise ValueError(f"{field_name} MongoDB invalide")
    return value


class OffreContactResponse(BaseModel):
    email: Optional[str] = None
    telephone: Optional[str] = None
    telephone_responsable: Optional[str] = None
    fax: Optional[str] = None
    responsable: Optional[str] = None
    site_web: Optional[str] = None
    lieu_depot: Optional[str] = None
    lieu_acquisition_dao: Optional[str] = None
    lieu_ouverture_plis: Optional[str] = None


class OffreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: Optional[str] = None
    secteur_id: Optional[str] = None
    titre: str
    organisme: str
    pays: str
    description: Optional[str] = None
    date_publication: Optional[datetime] = None
    date_limite: Optional[datetime] = None
    montant_estime: Optional[str] = None
    lien_source: Optional[str] = None
    contact: Optional[OffreContactResponse] = None
    hash_unique: Optional[str] = None
    date_scraping: Optional[datetime] = None
    acces_complet: bool = False

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "OffreResponse":
        return cls(
            id=str(doc["_id"]),
            source_id=str(doc["source_id"]) if doc.get("source_id") else None,
            secteur_id=str(doc["secteur_id"]) if doc.get("secteur_id") else None,
            titre=doc["titre"],
            organisme=doc["organisme"],
            pays=doc["pays"],
            description=doc.get("description"),
            date_publication=doc.get("date_publication"),
            date_limite=doc.get("date_limite"),
            montant_estime=doc.get("montant_estime"),
            lien_source=doc.get("lien_source"),
            contact=OffreContactResponse(**doc["contact"])
            if isinstance(doc.get("contact"), dict)
            else None,
            hash_unique=doc.get("hash_unique"),
            date_scraping=doc.get("date_scraping"),
            acces_complet=True,
        )


class PaginatedOffresResponse(BaseModel):
    items: list[OffreResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CalendrierOffreItem(BaseModel):
    id: str
    titre: str
    organisme: str
    pays: str
    date_limite: datetime


class CalendrierJourResponse(BaseModel):
    date: str
    offres: list[CalendrierOffreItem]


class CalendrierOffresResponse(BaseModel):
    year: int
    month: int
    jours: list[CalendrierJourResponse]
    total: int


class SecteurResponse(BaseModel):
    id: str
    nom: str
    mots_cles: list[str]
    nb_offres_actives: int

    @classmethod
    def from_mongo(cls, doc: dict[str, Any], nb_offres_actives: int = 0) -> "SecteurResponse":
        return cls(
            id=str(doc["_id"]),
            nom=doc["nom"],
            mots_cles=doc.get("mots_cles", []),
            nb_offres_actives=nb_offres_actives,
        )


class SourceResponse(BaseModel):
    id: str
    nom: str
    pays: str
    url_base: str
    type_scraping: ScrapingType
    actif: bool
    config: dict[str, Any] = Field(default_factory=dict)
    derniere_execution: Optional[datetime] = None

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "SourceResponse":
        return cls(
            id=str(doc["_id"]),
            nom=doc["nom"],
            pays=doc["pays"],
            url_base=doc["url_base"],
            type_scraping=doc["type_scraping"],
            actif=doc.get("actif", True),
            config=doc.get("config") or {},
            derniere_execution=doc.get("derniere_execution"),
        )


class SourceCreateRequest(BaseModel):
    nom: str = Field(min_length=2, max_length=200)
    pays: str = Field(min_length=2, max_length=100)
    url_base: HttpUrl
    type_scraping: ScrapingType = ScrapingType.HTML
    actif: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class SuiviSiteCreateRequest(BaseModel):
    url: HttpUrl
    pays: Optional[str] = Field(default=None, max_length=100)


class SuiviSiteResponse(BaseModel):
    id: str
    nom: str
    url_base: str
    actif: bool
    derniere_execution: Optional[datetime] = None
    dernier_statut: Optional[ScrapingStatus] = None
    nb_offres_trouvees: Optional[int] = None
    nb_offres_nouvelles: Optional[int] = None
    message_erreur: Optional[str] = None
    date_creation: Optional[datetime] = None


class LogScrapingResponse(BaseModel):
    id: str
    source_id: str
    date_execution: datetime
    statut: ScrapingStatus
    nb_offres_trouvees: int
    nb_offres_nouvelles: int
    message_erreur: Optional[str] = None

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "LogScrapingResponse":
        return cls(
            id=str(doc["_id"]),
            source_id=str(doc["source_id"]),
            date_execution=doc["date_execution"],
            statut=doc["statut"],
            nb_offres_trouvees=doc["nb_offres_trouvees"],
            nb_offres_nouvelles=doc["nb_offres_nouvelles"],
            message_erreur=doc.get("message_erreur"),
        )


class ScrapingTriggerRequest(BaseModel):
    source_id: str = Field(..., description="Identifiant MongoDB de la source à scraper")

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        return _require_object_id(value, "source_id")


class ScrapingTriggerResponse(BaseModel):
    source_id: str
    source_nom: str
    statut: ScrapingStatus
    nb_offres_trouvees: int
    nb_offres_nouvelles: int
    message_erreur: Optional[str] = None


class AbonneCreateRequest(BaseModel):
    email: Optional[EmailStr] = Field(
        default=None,
        description="Email (doit correspondre au compte connecté ; optionnel)",
    )
    secteurs_suivis: list[str] = Field(
        default_factory=list,
        description="IDs de secteurs à suivre (vide = tous)",
    )
    pays_suivis: list[str] = Field(
        default_factory=list,
        description="Pays à suivre (vide = tous)",
    )
    mots_cles_alertes: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Mots-clés optionnels pour affiner les alertes",
    )
    onboarding: bool = Field(
        default=False,
        description="Première configuration après inscription (au moins 1 secteur et 1 pays)",
    )

    @field_validator("secteurs_suivis")
    @classmethod
    def validate_secteurs(cls, values: list[str]) -> list[str]:
        for value in values:
            _require_object_id(value, "secteur_id")
        return values


class AbonneResponse(BaseModel):
    id: str
    email: str
    emails_supplementaires: list[str] = Field(default_factory=list)
    utilisateur_id: Optional[str] = None
    secteurs_suivis: list[str]
    pays_suivis: list[str]
    mots_cles_alertes: list[str] = Field(default_factory=list)
    preferences_configurees: bool = False
    actif: bool
    date_inscription: datetime

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "AbonneResponse":
        return cls(
            id=str(doc["_id"]),
            email=doc["email"],
            emails_supplementaires=doc.get("emails_supplementaires", []),
            utilisateur_id=str(doc["utilisateur_id"])
            if doc.get("utilisateur_id")
            else None,
            secteurs_suivis=[str(s) for s in doc.get("secteurs_suivis", [])],
            pays_suivis=doc.get("pays_suivis", []),
            mots_cles_alertes=[
                str(k).strip()
                for k in doc.get("mots_cles_alertes", [])
                if str(k).strip()
            ],
            preferences_configurees=bool(
                doc.get("preferences_configurees")
                or (doc.get("secteurs_suivis") and doc.get("pays_suivis"))
            ),
            actif=doc.get("actif", True),
            date_inscription=doc["date_inscription"],
        )


class AbonneEmailRequest(BaseModel):
    email: EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    prenom: Optional[str] = Field(default=None, max_length=100)
    nom: Optional[str] = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        error = validate_password_strength(value)
        if error:
            raise ValueError(error)
        return value


class VerifyEmailOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendEmailVerificationRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendResetOtpRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        error = validate_password_strength(value)
        if error:
            raise ValueError(error)
        return value


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        error = validate_password_strength(value)
        if error:
            raise ValueError(error)
        return value


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1)


class ForgotPasswordResponse(BaseModel):
    message: str


class VerifyResetOtpResponse(BaseModel):
    reset_token: str
    message: str = "Code vérifié. Vous pouvez choisir un nouveau mot de passe."


class MessageResponse(BaseModel):
    message: str


class RegisterResponse(BaseModel):
    status: str
    email: str
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., min_length=20)


class GoogleLinkRequest(BaseModel):
    link_token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=1)


class GoogleAuthResponse(BaseModel):
    status: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    link_token: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None


class GoogleConfigResponse(BaseModel):
    enabled: bool
    client_id: Optional[str] = None


class AppleAuthRequest(BaseModel):
    credential: str = Field(..., min_length=20)
    prenom: Optional[str] = None
    nom: Optional[str] = None


class AppleLinkRequest(BaseModel):
    link_token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=1)


class AppleAuthResponse(BaseModel):
    status: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    link_token: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None


class AppleConfigResponse(BaseModel):
    enabled: bool
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    date_inscription: datetime
    must_change_password: bool = False
    preferences_configurees: bool = False
    prenom: Optional[str] = None
    nom: Optional[str] = None
    photo_profil: Optional[str] = None
    auth_provider: Optional[str] = None
    email_verifie: bool = True
    statut_email: Optional[str] = None
    date_verification_email: Optional[datetime] = None

    @classmethod
    def from_mongo(
        cls,
        doc: dict[str, Any],
        *,
        preferences_configurees: bool = False,
    ) -> "UserResponse":
        email_verifie = doc.get("email_verifie")
        if email_verifie is None:
            email_verifie = True
        return cls(
            id=str(doc["_id"]),
            email=doc["email"],
            role=UserRole(doc["role"]),
            date_inscription=doc["date_inscription"],
            must_change_password=bool(doc.get("must_change_password")),
            preferences_configurees=preferences_configurees,
            prenom=doc.get("prenom"),
            nom=doc.get("nom"),
            photo_profil=doc.get("photo_profil"),
            auth_provider=doc.get("auth_provider"),
            email_verifie=bool(email_verifie),
            statut_email=doc.get("statut_email"),
            date_verification_email=doc.get("date_verification_email"),
        )


class AdminUtilisateurResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    date_inscription: datetime


class NotificationTriggerResponse(BaseModel):
    statut: NotificationStatus
    nb_emails_envoyes: int
    nb_echecs: int
    nb_offres_recentes: int
    message_erreur: Optional[str] = None


class NotificationPreviewResponse(BaseModel):
    statut: NotificationStatus
    nb_emails_envoyes: int
    nb_offres: int
    message_erreur: Optional[str] = None


class LogNotificationResponse(BaseModel):
    id: str
    date_execution: datetime
    statut: NotificationStatus
    nb_emails_envoyes: int
    nb_echecs: int
    message_erreur: Optional[str] = None

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "LogNotificationResponse":
        return cls(
            id=str(doc["_id"]),
            date_execution=doc["date_execution"],
            statut=NotificationStatus(doc["statut"]),
            nb_emails_envoyes=doc.get("nb_emails_envoyes", 0),
            nb_echecs=doc.get("nb_echecs", 0),
            message_erreur=doc.get("message_erreur"),
        )
