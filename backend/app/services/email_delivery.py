"""Envoi d'emails transactionnels (SMTP ou Resend).

Formspree n'est pas utilisé ici : il enregistre une soumission et notifie le
propriétaire du formulaire, mais n'envoie pas le HTML à une adresse arbitraire
sans plugin Autoresponse configuré dans le tableau de bord.
"""

from __future__ import annotations

import base64
import logging
import re

import resend
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.db.config import settings
from app.services.email_templates import LOGO_CID, resolve_logo_file

logger = logging.getLogger(__name__)

_DEFAULT_RESEND_FROM = "MarchéConnect <onboarding@resend.dev>"


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user)


def _smtp_ready() -> bool:
    return _smtp_configured() and bool(settings.smtp_password.strip())


def _resend_configured() -> bool:
    return bool(settings.resend_api_key)


def _smtp_from_addresses() -> tuple[str, str]:
    """Retourne (en-tête From, adresse enveloppe SMTP)."""
    raw = (settings.smtp_from or settings.smtp_user).strip()
    if "<" in raw and ">" in raw:
        match = re.search(r"<([^>]+)>", raw)
        envelope = match.group(1).strip() if match else settings.smtp_user
        return raw, envelope
    display = settings.smtp_from_name or "MarchéConnect"
    envelope = raw
    return formataddr((display, envelope)), envelope


def _resend_from_address() -> str:
    from_addr = settings.resend_from_email.strip()
    if not from_addr:
        return _DEFAULT_RESEND_FROM
    if "<" not in from_addr:
        return f"MarchéConnect <{from_addr}>"
    return from_addr


def _inline_images_for_html(html_body: str) -> dict[str, tuple[bytes, str]]:
    """Pièces jointes inline (CID) référencées dans le HTML."""
    inline: dict[str, tuple[bytes, str]] = {}
    if f"cid:{LOGO_CID}" not in html_body:
        return inline

    logo_path = resolve_logo_file()
    if logo_path is not None:
        inline[LOGO_CID] = (logo_path.read_bytes(), "image/png")
    return inline


def _attach_inline_images(
    msg: MIMEMultipart,
    inline_images: dict[str, tuple[bytes, str]],
) -> None:
    for content_id, (data, mime_type) in inline_images.items():
        subtype = mime_type.split("/")[-1]
        part = MIMEImage(data, _subtype=subtype)
        part.add_header("Content-ID", f"<{content_id}>")
        part.add_header("Content-Disposition", "inline", filename="I1.png")
        msg.attach(part)


def _send_via_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    *,
    inline_images: dict[str, tuple[bytes, str]] | None = None,
) -> None:
    header_from, envelope_from = _smtp_from_addresses()
    inline_images = inline_images or {}

    if inline_images:
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = header_from
        msg["To"] = to_email
        alternative = MIMEMultipart("alternative")
        alternative.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alternative)
        _attach_inline_images(msg, inline_images)
    else:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = header_from
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(envelope_from, [to_email], msg.as_string())

    logger.info("Email SMTP envoyé à %s", to_email)


def _send_via_resend(
    to_email: str,
    subject: str,
    html_body: str,
    *,
    inline_images: dict[str, tuple[bytes, str]] | None = None,
) -> None:
    resend.api_key = settings.resend_api_key
    params: resend.Emails.SendParams = {
        "from": _resend_from_address(),
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }
    if inline_images:
        params["attachments"] = [
            {
                "filename": "I1.png",
                "content": base64.b64encode(data).decode("ascii"),
                "content_id": content_id,
            }
            for content_id, (data, _mime) in inline_images.items()
        ]
    resend.Emails.send(params)
    logger.info("Email Resend envoyé à %s", to_email)


def send_html_email(to_email: str, subject: str, html_body: str) -> None:
    """Envoie un email HTML à n'importe quelle adresse valide."""
    errors: list[str] = []
    inline_images = _inline_images_for_html(html_body)

    if _smtp_ready():
        try:
            _send_via_smtp(to_email, subject, html_body, inline_images=inline_images)
            return
        except Exception as exc:
            errors.append(f"SMTP: {exc}")
            logger.warning("Échec SMTP vers %s : %s", to_email, exc)

    if _resend_configured():
        try:
            _send_via_resend(to_email, subject, html_body, inline_images=inline_images)
            return
        except Exception as exc:
            errors.append(f"Resend: {exc}")
            logger.warning("Échec Resend vers %s : %s", to_email, exc)

    if not (_smtp_configured() or _resend_configured()):
        raise ValueError(
            "Aucun service email configuré. Renseignez "
            "SMTP_HOST/SMTP_USER/SMTP_PASSWORD ou RESEND_API_KEY dans .env"
        )

    if _smtp_configured() and not settings.smtp_password.strip():
        raise ValueError(
            "SMTP_PASSWORD manquant — créez un mot de passe d'application Gmail "
            "(https://myaccount.google.com/apppasswords) et ajoutez-le dans .env"
        )

    raise RuntimeError("; ".join(errors))


def email_delivery_ready() -> bool:
    """True si au moins un canal peut envoyer à n'importe quelle adresse client."""
    return _smtp_ready()


def log_email_config_status() -> None:
    if _smtp_ready():
        logger.info(
            "Emails transactionnels : SMTP actif (%s)",
            settings.smtp_user,
        )
        return

    if _smtp_configured() and not settings.smtp_password.strip():
        logger.error(
            "Emails transactionnels INACTIFS : SMTP_PASSWORD manquant dans .env. "
            "Créez un mot de passe d'application Gmail : "
            "https://myaccount.google.com/apppasswords"
        )
        return

    if _resend_configured():
        logger.warning(
            "Emails transactionnels : Resend configuré mais en mode test "
            "(onboarding@resend.dev) — envoi limité. Préférez SMTP Gmail en dev."
        )
        return

    logger.error(
        "Emails transactionnels INACTIFS : configurez SMTP ou Resend dans .env"
    )
