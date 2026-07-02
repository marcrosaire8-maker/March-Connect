"""Emails transactionnels (bienvenue, mot de passe, activation des alertes)."""

from __future__ import annotations

import html
import logging

from app.db.config import settings
from app.services.notification_interval import notification_interval_label
from app.services.email_delivery import send_html_email
from app.services.email_templates import (
    BRAND,
    BRAND_LIGHT,
    MUTED,
    TEXT,
    email_button,
    email_highlight_box,
    email_shell,
    email_steps,
)

logger = logging.getLogger(__name__)


def send_temp_password_email(to_email: str, temp_password: str) -> None:
    safe_password = html.escape(temp_password)
    body = f"""
    <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{TEXT};">
      Vous avez demandé à réinitialiser votre mot de passe. Utilisez le code ci-dessous
      pour vous connecter, puis choisissez un nouveau mot de passe personnel.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <div style="display:inline-block;background:{BRAND_LIGHT};border:2px dashed {BRAND};
      border-radius:12px;padding:18px 32px;font-size:24px;font-weight:800;
      letter-spacing:3px;font-family:monospace;color:{TEXT};">
        {safe_password}
      </div>
    </div>
    <p style="margin:0;font-size:13px;line-height:1.6;color:{MUTED};">
      Si vous n'êtes pas à l'origine de cette demande, ignorez cet email et contactez le support.
    </p>
    """
    send_html_email(
        to_email,
        "Votre mot de passe provisoire — MarchéConnect",
        email_shell(
            eyebrow="Sécurité",
            title="Mot de passe provisoire",
            body_html=body,
        ),
    )


def send_password_reset_otp_email(to_email: str, otp: str) -> None:
    safe_otp = html.escape(otp)
    body = f"""
    <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{TEXT};">
      Vous avez demandé à réinitialiser votre mot de passe. Saisissez le code ci-dessous
      sur la page de vérification pour continuer.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <div style="display:inline-block;background:{BRAND_LIGHT};border:2px dashed {BRAND};
      border-radius:12px;padding:18px 32px;font-size:28px;font-weight:800;
      letter-spacing:6px;font-family:monospace;color:{TEXT};">
        {safe_otp}
      </div>
    </div>
    <p style="margin:0;font-size:13px;line-height:1.6;color:{MUTED};">
      Ce code expire dans <strong>10 minutes</strong>. Si vous n'êtes pas à l'origine
      de cette demande, ignorez cet email.
    </p>
    """
    send_html_email(
        to_email,
        "Code de réinitialisation — MarchéConnect",
        email_shell(
            eyebrow="Sécurité",
            title="Votre code temporaire",
            body_html=body,
        ),
    )


def send_email_verification_otp_email(to_email: str, otp: str) -> None:
    safe_otp = html.escape(otp)
    body = f"""
    <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{TEXT};">
      Bienvenue sur MarchéConnect. Pour activer votre compte, saisissez le code
      de vérification ci-dessous sur la page d'inscription.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <div style="display:inline-block;background:{BRAND_LIGHT};border:2px dashed {BRAND};
      border-radius:12px;padding:18px 32px;font-size:28px;font-weight:800;
      letter-spacing:6px;font-family:monospace;color:{TEXT};">
        {safe_otp}
      </div>
    </div>
    <p style="margin:0;font-size:13px;line-height:1.6;color:{MUTED};">
      Ce code expire dans <strong>10 minutes</strong>. Tant que votre email n'est pas
      vérifié, vous ne pourrez pas vous connecter.
    </p>
    """
    send_html_email(
        to_email,
        "Vérifiez votre adresse email — MarchéConnect",
        email_shell(
            eyebrow="Activation",
            title="Confirmez votre email",
            body_html=body,
        ),
    )


def send_welcome_email(to_email: str) -> None:
    app_url = settings.frontend_url.rstrip("/")
    interval_label = notification_interval_label()
    body = f"""
    <p style="margin:0 0 20px;font-size:16px;line-height:1.65;color:{TEXT};">
      Félicitations, votre compte est prêt. MarchéConnect vous aide à ne manquer aucun
      appel d'offres pertinent pour votre activité.
    </p>
    {email_steps([
        "Choisissez vos secteurs et votre pays dans Mon compte",
        "Recevez automatiquement les nouvelles offres par email",
        f"Consultez les détails et postulez en un clic",
    ])}
    {email_button(f"{app_url}/mon-compte", "Configurer mes préférences")}
    <p style="margin:0;font-size:13px;line-height:1.6;color:{MUTED};">
      Dès que vos critères sont enregistrés, vos alertes partent
      <strong>{interval_label}</strong> — uniquement les nouvelles offres qui vous correspondent.
    </p>
    """
    send_html_email(
        to_email,
        "Bienvenue sur MarchéConnect",
        email_shell(
            eyebrow="Bienvenue",
            title="Votre compte est créé",
            body_html=body,
            footer_note="MarchéConnect — Ne ratez plus les marchés publics qui vous intéressent",
        ),
    )


def send_alerts_activated_email(to_email: str, criteria_label: str) -> None:
    safe_criteria = html.escape(criteria_label)
    interval_label = notification_interval_label()
    app_url = settings.frontend_url.rstrip("/")
    body = f"""
    <p style="margin:0 0 8px;font-size:16px;line-height:1.65;color:{TEXT};">
      Parfait — vos alertes sont maintenant actives. Voici la sélection que nous surveillons
      pour vous :
    </p>
    {email_highlight_box(safe_criteria)}
    <p style="margin:0 0 8px;font-size:15px;line-height:1.65;color:{TEXT};">
      Dès qu'une nouvelle offre correspond à ces critères, vous la recevrez par email
      automatiquement, <strong>{interval_label}</strong>.
    </p>
    {email_button(f"{app_url}/offres", "Voir mes offres")}
    <p style="margin:0;font-size:13px;line-height:1.6;color:{MUTED};">
      Vous pouvez modifier vos secteurs, pays ou emails d'alerte à tout moment depuis Mon compte.
    </p>
    """
    send_html_email(
        to_email,
        "Alertes activées — MarchéConnect",
        email_shell(
            eyebrow="Alertes RSS",
            title="C'est parti !",
            body_html=body,
            footer_note=f"Alertes automatiques {interval_label} — MarchéConnect",
        ),
    )


def send_welcome_email_safe(to_email: str) -> None:
    try:
        send_welcome_email(to_email)
    except Exception as exc:
        logger.warning("Email de bienvenue non envoyé à %s : %s", to_email, exc)


def send_alerts_activated_email_safe(to_email: str, criteria_label: str) -> None:
    try:
        send_alerts_activated_email(to_email, criteria_label)
    except Exception as exc:
        logger.warning(
            "Email d'activation des alertes non envoyé à %s : %s", to_email, exc
        )
