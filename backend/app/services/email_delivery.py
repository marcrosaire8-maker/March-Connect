"""Envoi d'emails transactionnels via SMTP (local et production)."""

from __future__ import annotations

import logging
import re
import smtplib
import time
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.db.config import settings
from app.services.email_templates import LOGO_CID, resolve_logo_file

logger = logging.getLogger(__name__)

_RETRY_DELAYS_SECONDS = (2, 5, 10)


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user)


def _smtp_ready() -> bool:
    return _smtp_configured() and bool(settings.smtp_password.strip())


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


def _send_via_smtp_once(
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


def send_html_email(to_email: str, subject: str, html_body: str) -> None:
    """Envoie un email HTML via SMTP avec nouvelles tentatives en cas d'échec."""
    if not _smtp_ready():
        if _smtp_configured() and not settings.smtp_password.strip():
            raise ValueError(
                "SMTP_PASSWORD manquant — configurez la clé SMTP Brevo ou un mot de passe "
                "d'application Gmail dans .env"
            )
        raise ValueError(
            "SMTP non configuré. Renseignez SMTP_HOST, SMTP_USER et SMTP_PASSWORD."
        )

    inline_images = _inline_images_for_html(html_body)
    errors: list[str] = []

    for attempt, delay in enumerate((0, *_RETRY_DELAYS_SECONDS), start=1):
        if delay:
            time.sleep(delay)
        try:
            _send_via_smtp_once(
                to_email,
                subject,
                html_body,
                inline_images=inline_images,
            )
            logger.info("Email SMTP envoyé à %s (tentative %d)", to_email, attempt)
            return
        except Exception as exc:
            message = f"tentative {attempt}: {exc}"
            errors.append(message)
            logger.warning("Échec SMTP vers %s — %s", to_email, message)

    raise RuntimeError("; ".join(errors))


def email_delivery_ready() -> bool:
    return _smtp_ready()


def log_email_config_status() -> None:
    if _smtp_ready():
        logger.info(
            "Emails transactionnels : SMTP actif (%s via %s)",
            settings.smtp_user,
            settings.smtp_host,
        )
        return

    if _smtp_configured() and not settings.smtp_password.strip():
        logger.error(
            "Emails transactionnels INACTIFS : SMTP_PASSWORD manquant dans .env"
        )
        return

    logger.error(
        "Emails transactionnels INACTIFS : configurez SMTP_HOST, SMTP_USER, SMTP_PASSWORD"
    )
