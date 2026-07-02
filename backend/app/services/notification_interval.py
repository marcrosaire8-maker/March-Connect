"""Libellés et fenêtres temporelles pour les alertes email."""

from __future__ import annotations

from app.db.config import settings


def notification_interval_minutes() -> int:
    return max(1, settings.notification_interval_minutes)


def notification_interval_label() -> str:
    minutes = notification_interval_minutes()
    if minutes == 1:
        return "chaque minute"
    if minutes < 60:
        return f"toutes les {minutes} minutes"
    hours, remainder = divmod(minutes, 60)
    if remainder == 0:
        return "chaque heure" if hours == 1 else f"toutes les {hours} heures"
    return f"toutes les {minutes} minutes"


def notification_lookback_period_label() -> str:
    minutes = notification_interval_minutes()
    if minutes == 1:
        return "la dernière minute"
    if minutes < 60:
        return f"les {minutes} dernières minutes"
    hours, remainder = divmod(minutes, 60)
    if remainder == 0:
        return "la dernière heure" if hours == 1 else f"les {hours} dernières heures"
    return f"les {minutes} dernières minutes"


def notification_availability_label() -> str:
    """Libellé pour les alertes basées sur les offres encore ouvertes."""
    return "dont la date limite n'est pas encore atteinte"
