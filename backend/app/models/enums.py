from enum import Enum


class ScrapingType(str, Enum):
    HTML = "html"
    API = "api"
    RSS = "rss"


class ScrapingStatus(str, Enum):
    SUCCES = "succes"
    ECHEC = "echec"
    PARTIEL = "partiel"


class NotificationStatus(str, Enum):
    SUCCES = "succes"
    ECHEC = "echec"
    PARTIEL = "partiel"


class UserRole(str, Enum):
    CLIENT = "client"
    ADMIN = "admin"


class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"
    BOTH = "both"


class EmailVerificationStatus(str, Enum):
    VERIFIE = "verifie"
    NON_VERIFIE = "non_verifie"
    EN_ATTENTE = "en_attente"
