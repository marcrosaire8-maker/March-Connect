"""Tests de la rotation des offres dans les alertes email."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from bson import ObjectId

from app.services.notifications import NotificationService


def _offre(oid: ObjectId, titre: str = "Offre test") -> dict:
    return {
        "_id": oid,
        "titre": titre,
        "organisme": "Org",
        "pays": "Bénin",
        "secteur_nom": "Agriculture",
    }


def test_pick_prefers_unnotified_offres():
    service = NotificationService()
    db = MagicMock()
    abonne_id = ObjectId()
    o1, o2 = ObjectId(), ObjectId()

    service._fetch_active_offres_for_abonne = MagicMock(  # type: ignore[method-assign]
        return_value=[_offre(o1), _offre(o2)]
    )

    picked = service._pick_offres_for_scheduled_send(
        db,
        {"email": "user@example.com", "secteurs_suivis": [], "pays_suivis": ["Bénin"]},
        abonne_id,
        already_notified={o1},
        max_offres=1,
    )

    assert len(picked) == 1
    assert picked[0]["_id"] == o2


def test_pick_rotates_when_all_notified():
    service = NotificationService()
    db = MagicMock()
    abonne_id = ObjectId()
    o1, o2 = ObjectId(), ObjectId()
    old = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recent = datetime(2026, 6, 1, tzinfo=timezone.utc)

    service._fetch_active_offres_for_abonne = MagicMock(  # type: ignore[method-assign]
        return_value=[_offre(o1), _offre(o2)]
    )
    service._notification_sent_at_by_offre = MagicMock(  # type: ignore[method-assign]
        return_value={o1: recent, o2: old}
    )

    picked = service._pick_offres_for_scheduled_send(
        db,
        {"email": "user@example.com"},
        abonne_id,
        already_notified={o1, o2},
        max_offres=1,
    )

    assert picked[0]["_id"] == o2
