"""Construction et normalisation des coordonnées de contact des offres."""

from __future__ import annotations

import re
from typing import Any

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
PHONE_RE = re.compile(
    r"(?:\+?\d{1,4}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}"
)

CONTACT_FIELDS = (
    "email",
    "telephone",
    "telephone_responsable",
    "fax",
    "responsable",
    "site_web",
    "lieu_depot",
    "lieu_acquisition_dao",
    "lieu_ouverture_plis",
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _is_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 8 <= len(digits) <= 15


def _normalize_benin_digits(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if digits.startswith("229"):
        digits = digits[3:]
    if digits.startswith("0") and len(digits) == 9:
        digits = digits[1:]
    return digits


def is_valid_benin_phone(value: str) -> bool:
    """Filtre les numéros manifestement invalides renvoyés par certaines APIs."""
    digits = _normalize_benin_digits(value)
    if len(digits) != 8:
        return False
    if digits.startswith("00"):
        return False
    if digits[0] not in "23456789":
        return False
    if len(set(digits)) <= 2:
        return False
    return True


def sanitize_benin_phone(value: str | None) -> str:
    text = _clean(value)
    if not text or not is_valid_benin_phone(text):
        return ""
    return text


def normalize_contact(data: dict[str, Any] | None) -> dict[str, str] | None:
    if not data:
        return None
    cleaned: dict[str, str] = {}
    for key in CONTACT_FIELDS:
        text = _clean(data.get(key))
        if text:
            cleaned[key] = text
    return cleaned or None


def merge_contacts(*parts: dict[str, Any] | None) -> dict[str, str] | None:
    merged: dict[str, str] = {}
    for part in parts:
        normalized = normalize_contact(part)
        if not normalized:
            continue
        for key, value in normalized.items():
            if key not in merged:
                merged[key] = value
    return merged or None


def contact_from_description(description: str | None) -> dict[str, str] | None:
    text = _clean(description)
    if not text:
        return None

    contact: dict[str, str] = {}
    emails = EMAIL_RE.findall(text)
    if emails:
        contact["email"] = emails[0].lower()

    for match in PHONE_RE.findall(text):
        if _is_phone(match):
            contact.setdefault("telephone", match.strip())
            break

    return normalize_contact(contact)


def contact_from_marches_publics_bj(item: dict[str, Any]) -> dict[str, str] | None:
    autorite = item.get("autoriteContractante") or {}
    contact: dict[str, str] = {}

    email = _clean(autorite.get("email"))
    if email:
        contact["email"] = email.lower()

    telephone = sanitize_benin_phone(autorite.get("telephone"))
    if telephone:
        contact["telephone"] = telephone

    fax = _clean(autorite.get("fax"))
    if fax:
        contact["fax"] = fax

    responsable = _clean(autorite.get("responsable"))
    if responsable:
        contact["responsable"] = responsable

    site_web = _clean(autorite.get("urlsiteweb"))
    if site_web:
        contact["site_web"] = site_web

    tel_resp = sanitize_benin_phone(item.get("dosTelResp"))
    if tel_resp:
        contact["telephone_responsable"] = tel_resp

    lieu_depot = _clean(item.get("dosLieuDepotDossier"))
    if lieu_depot:
        contact["lieu_depot"] = lieu_depot

    lieu_dao = _clean(item.get("doslieuacquisitiondao"))
    if lieu_dao:
        contact["lieu_acquisition_dao"] = lieu_dao

    lieu_plis = _clean(item.get("dosLieuOuvertureDesPlis"))
    if lieu_plis:
        contact["lieu_ouverture_plis"] = lieu_plis

    return merge_contacts(contact, contact_from_description(item.get("dosDescriptif")))


def enrich_offre_contact(offre: dict[str, Any]) -> dict[str, Any]:
    """Complète le champ contact à partir des données structurées et de la description."""
    merged = merge_contacts(
        offre.get("contact"),
        contact_from_description(offre.get("description")),
    )
    if merged:
        offre["contact"] = merged
    else:
        offre.pop("contact", None)
    return offre
