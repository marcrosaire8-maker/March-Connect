"""Gabarits HTML partagés pour les emails MarchéConnect."""

from __future__ import annotations

import html
from pathlib import Path

from app.db.config import settings

BRAND = "#059669"
BRAND_DARK = "#047857"
BRAND_LIGHT = "#ecfdf5"
BG = "#f1f5f9"
TEXT = "#0f172a"
MUTED = "#64748b"
BORDER = "#e2e8f0"
SITE_NAME = "MarchéConnect"
LOGO_MARK_TEXT = "MC"
LOGO_ASSET_PATH = "/I1.png"
LOGO_CID = "marcheconnect-logo"
LOGO_SIZE = 44

_REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_logo_file() -> Path | None:
    """Chemin vers le logo officiel I1.png (frontend/public ou racine du dépôt)."""
    for candidate in (
        _REPO_ROOT / "frontend" / "public" / "I1.png",
        _REPO_ROOT / "I1.png",
    ):
        if candidate.is_file():
            return candidate
    return None


def _public_logo_url() -> str:
    base_url = settings.frontend_url.rstrip("/")
    if not base_url or "localhost" in base_url or "127.0.0.1" in base_url:
        return ""
    return f"{base_url}{LOGO_ASSET_PATH}"


def email_logo_src() -> str:
    """URL publique ou référence CID pour l'image inline dans les emails."""
    if resolve_logo_file() is not None:
        return f"cid:{LOGO_CID}"
    return _public_logo_url()


def email_logo() -> str:
    logo_src = email_logo_src()
    if logo_src:
        safe_src = html.escape(logo_src)
        image = f"""<img src="{safe_src}" width="{LOGO_SIZE}" height="{LOGO_SIZE}" alt="{SITE_NAME}"
        style="display:block;width:{LOGO_SIZE}px;height:{LOGO_SIZE}px;border-radius:10px;object-fit:contain;">"""
    else:
        image = f"""<span style="display:block;width:{LOGO_SIZE}px;height:{LOGO_SIZE}px;line-height:{LOGO_SIZE}px;
        text-align:center;border-radius:10px;background:#ffffff;color:{BRAND_DARK};
        font-size:15px;font-weight:900;letter-spacing:-0.04em;">{LOGO_MARK_TEXT}</span>"""
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 22px;">
      <tr>
        <td style="vertical-align:middle;width:48px;">{image}</td>
        <td style="vertical-align:middle;padding-left:12px;">
          <div style="font-size:19px;line-height:1;font-weight:900;color:#ffffff;">
            Marché<span style="color:#d1fae5;">Connect</span>
          </div>
          <div style="margin-top:5px;font-size:11px;letter-spacing:0.08em;
          text-transform:uppercase;color:rgba(255,255,255,0.76);">
            Appels d'offres ciblés
          </div>
        </td>
      </tr>
    </table>
    """


def email_button(href: str, label: str) -> str:
    safe_href = html.escape(href)
    safe_label = html.escape(label)
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" style="margin:28px 0;">
      <tr>
        <td style="border-radius:10px;background:{BRAND};">
          <a href="{safe_href}"
             style="display:inline-block;padding:14px 28px;font-size:15px;font-weight:700;
             color:#ffffff;text-decoration:none;border-radius:10px;">
            {safe_label}
          </a>
        </td>
      </tr>
    </table>
    """


def email_highlight_box(content: str) -> str:
    return f"""
    <div style="background:{BRAND_LIGHT};border-left:4px solid {BRAND};border-radius:0 10px 10px 0;
    padding:16px 18px;margin:20px 0;font-size:15px;font-weight:600;color:{BRAND_DARK};">
      {content}
    </div>
    """


def email_steps(items: list[str]) -> str:
    rows = []
    for index, item in enumerate(items, start=1):
        rows.append(
            f"""
            <tr>
              <td style="vertical-align:top;padding:0 14px 16px 0;width:32px;">
                <div style="width:28px;height:28px;line-height:28px;text-align:center;
                background:{BRAND};color:#fff;border-radius:50%;font-size:13px;font-weight:700;">
                  {index}
                </div>
              </td>
              <td style="vertical-align:top;padding-bottom:16px;color:{TEXT};font-size:15px;line-height:1.55;">
                {html.escape(item)}
              </td>
            </tr>
            """
        )
    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:8px 0 20px;">
      {''.join(rows)}
    </table>
    """


def email_shell(
    *,
    eyebrow: str,
    title: str,
    body_html: str,
    footer_note: str | None = None,
) -> str:
    safe_eyebrow = html.escape(eyebrow)
    safe_title = html.escape(title)
    safe_footer = html.escape(footer_note or f"© {SITE_NAME} — Appels d'offres sur mesure")
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title}</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:'Segoe UI',Arial,Helvetica,sans-serif;
color:{TEXT};-webkit-font-smoothing:antialiased;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{BG};padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
               style="max-width:600px;background:#ffffff;border-radius:16px;overflow:hidden;
               box-shadow:0 4px 24px rgba(15,23,42,0.08);">
          <tr>
            <td style="background:linear-gradient(135deg,{BRAND} 0%,{BRAND_DARK} 100%);
            padding:28px 32px;">
              {email_logo()}
              <p style="margin:0 0 6px;font-size:12px;font-weight:700;letter-spacing:0.12em;
              text-transform:uppercase;color:rgba(255,255,255,0.85);">{safe_eyebrow}</p>
              <h1 style="margin:0;font-size:26px;line-height:1.25;font-weight:800;color:#ffffff;">
                {safe_title}
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              {body_html}
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px 28px;border-top:1px solid {BORDER};background:#fafafa;">
              <p style="margin:0;font-size:12px;line-height:1.6;color:{MUTED};text-align:center;">
                {safe_footer}
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def email_offer_card(
    *,
    titre: str,
    organisme: str,
    pays: str,
    secteur: str,
    date_limite: str,
    lien: str,
    contact_html: str,
) -> str:
    safe_titre = html.escape(titre)
    safe_org = html.escape(organisme)
    safe_pays = html.escape(pays)
    safe_secteur = html.escape(secteur)
    safe_date = html.escape(date_limite)
    safe_lien = html.escape(lien)

    secteur_chip = (
        f"""<span style="display:inline-block;background:{BRAND_LIGHT};color:{BRAND_DARK};
        font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;
        letter-spacing:0.02em;margin-bottom:10px;">{safe_secteur}</span>"""
        if secteur
        else ""
    )
    title_block = (
        f"""<a href="{safe_lien}" style="color:{TEXT};text-decoration:none;font-size:17px;
        font-weight:700;line-height:1.4;">{safe_titre}</a>"""
        if lien
        else f"""<span style="font-size:17px;font-weight:700;line-height:1.4;">{safe_titre}</span>"""
    )
    cta = (
        f"""<a href="{safe_lien}" style="display:inline-block;margin-top:14px;padding:10px 18px;
        background:{BRAND};color:#fff;font-size:13px;font-weight:700;text-decoration:none;
        border-radius:8px;">Accéder à l'offre →</a>"""
        if lien
        else ""
    )
    contact_block = (
        f"""<div style="margin-top:12px;padding-top:12px;border-top:1px dashed {BORDER};
        font-size:13px;line-height:1.6;color:{MUTED};">{contact_html}</div>"""
        if contact_html
        else ""
    )

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
           style="margin-bottom:16px;border:1px solid {BORDER};border-left:4px solid {BRAND};
           border-radius:0 12px 12px 0;background:#ffffff;">
      <tr>
        <td style="padding:18px 20px;">
          {secteur_chip}
          <div style="margin-bottom:8px;">{title_block}</div>
          <p style="margin:0 0 6px;font-size:14px;color:{MUTED};">{safe_org} · {safe_pays}</p>
          <p style="margin:0;font-size:13px;color:{TEXT};">
            <strong style="color:{BRAND_DARK};">Date limite</strong> — {safe_date}
          </p>
          {contact_block}
          {cta}
        </td>
      </tr>
    </table>
    """
