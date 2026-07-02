"""Rappels email avant échéance des offres (J-7, J-3, J-1)."""

from __future__ import annotations

import html
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

from app.db.config import settings
from app.services.abonne_prefs import (
    abonne_has_active_preferences,
    abonne_preference_lists,
    offre_matches_keywords,
)
from app.services.email_delivery import send_html_email
from app.services.email_templates import MUTED, TEXT, email_button, email_shell
from app.services.offre_filters import active_deadline_filter, merge_mongo_filters

logger = logging.getLogger(__name__)

REMINDER_DAYS = (7, 3, 1)


class DeadlineReminderService:
    def __init__(self) -> None:
        self._client: MongoClient | None = None

    def _get_db(self):
        if self._client is None:
            self._client = MongoClient(settings.mongodb_uri)
        return self._client[settings.mongodb_db_name]

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    @staticmethod
    def _day_window(days_before: int) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        target = (now + timedelta(days=days_before)).date()
        start = datetime(target.year, target.month, target.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        return start, end

    def _eligible_abonnes(self, db) -> list[dict[str, Any]]:
        return list(
            db.abonnes.find(
                {
                    "actif": True,
                    "utilisateur_id": {"$exists": True, "$ne": None},
                }
            )
        )

    @staticmethod
    def _offre_matches_abonne(offre: dict[str, Any], abonne: dict[str, Any]) -> bool:
        secteurs, pays = abonne_preference_lists(abonne)
        if pays and offre.get("pays") not in pays:
            return False
        if secteurs:
            secteur_id = offre.get("secteur_id")
            if secteur_id is None:
                return False
            if str(secteur_id) not in {str(s) for s in secteurs}:
                return False
        return offre_matches_keywords(offre, abonne)

    def _already_sent(
        self,
        db,
        abonne_id: ObjectId,
        offre_id: ObjectId,
        days_before: int,
    ) -> bool:
        return (
            db.rappels_envoyes.find_one(
                {
                    "abonne_id": abonne_id,
                    "offre_id": offre_id,
                    "jours_avant": days_before,
                }
            )
            is not None
        )

    def _mark_sent(
        self,
        db,
        abonne_id: ObjectId,
        offre_id: ObjectId,
        days_before: int,
    ) -> None:
        try:
            db.rappels_envoyes.insert_one(
                {
                    "abonne_id": abonne_id,
                    "offre_id": offre_id,
                    "jours_avant": days_before,
                    "date_envoi": datetime.now(timezone.utc),
                }
            )
        except BulkWriteError:
            pass

    @staticmethod
    def _build_email(
        offre: dict[str, Any],
        days_before: int,
        app_url: str,
    ) -> tuple[str, str]:
        titre = html.escape(offre.get("titre", ""))
        organisme = html.escape(offre.get("organisme", ""))
        pays = html.escape(offre.get("pays", ""))
        date_limite = offre.get("date_limite")
        date_label = (
            date_limite.astimezone(timezone.utc).strftime("%d/%m/%Y")
            if isinstance(date_limite, datetime)
            else "Non précisée"
        )
        detail_url = f"{app_url.rstrip('/')}/offres/{offre['_id']}"
        body = f"""
        <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{TEXT};">
          L'offre ci-dessous arrive à échéance dans <strong>{days_before} jour(s)</strong>.
        </p>
        <div style="border:1px solid #e2e8f0;border-left:4px solid #059669;border-radius:0 12px 12px 0;padding:18px 20px;margin:0 0 20px;">
          <p style="margin:0 0 8px;font-size:17px;font-weight:700;color:{TEXT};">{titre}</p>
          <p style="margin:0 0 6px;font-size:14px;color:{MUTED};">{organisme} · {pays}</p>
          <p style="margin:0;font-size:14px;color:{TEXT};"><strong>Date limite :</strong> {date_label}</p>
        </div>
        {email_button(detail_url, "Voir l'offre")}
        """
        subject = f"[MarchéConnect] Échéance J-{days_before} — {offre.get('titre', 'Offre')[:60]}"
        html_body = email_shell(
            eyebrow="Rappel échéance",
            title=f"J-{days_before} avant la date limite",
            body_html=body,
            footer_note="Rappels automatiques MarchéConnect",
        )
        return subject, html_body

    def run(self) -> dict[str, int]:
        sent = 0
        errors = 0
        db = self._get_db()
        app_url = settings.frontend_url

        try:
            abonnes = [
                ab for ab in self._eligible_abonnes(db) if abonne_has_active_preferences(ab)
            ]
            favori_map: dict[ObjectId, set[ObjectId]] = {}
            for fav in db.favoris.find({}, {"utilisateur_id": 1, "offre_id": 1}):
                uid = fav.get("utilisateur_id")
                oid = fav.get("offre_id")
                if isinstance(uid, ObjectId) and isinstance(oid, ObjectId):
                    favori_map.setdefault(uid, set()).add(oid)

            for days_before in REMINDER_DAYS:
                start, end = self._day_window(days_before)
                query = merge_mongo_filters(
                    active_deadline_filter(include_without_deadline=False),
                    {"date_limite": {"$gte": start, "$lt": end}},
                )
                offres = list(db.offres.find(query))

                for abonne in abonnes:
                    abonne_id = abonne["_id"]
                    user_id = abonne.get("utilisateur_id")
                    fav_ids: set[ObjectId] = set()
                    if user_id is not None:
                        fav_ids = favori_map.get(user_id, set())
                        if not fav_ids and isinstance(user_id, ObjectId):
                            fav_ids = favori_map.get(str(user_id), set())

                    for offre in offres:
                        is_fav = offre["_id"] in fav_ids
                        matches = self._offre_matches_abonne(offre, abonne)
                        if not is_fav and not matches:
                            continue
                        if self._already_sent(db, abonne_id, offre["_id"], days_before):
                            continue

                        subject, html_body = self._build_email(offre, days_before, app_url)
                        try:
                            send_html_email(abonne["email"], subject, html_body)
                            self._mark_sent(db, abonne_id, offre["_id"], days_before)
                            sent += 1
                        except Exception as exc:
                            errors += 1
                            logger.warning(
                                "Rappel J-%d non envoyé à %s : %s",
                                days_before,
                                abonne["email"],
                                exc,
                            )

            return {"envoyes": sent, "echecs": errors}
        finally:
            self.close()
