"""Envoi automatique des alertes email (offres actives selon les préférences de chaque abonné)."""

from __future__ import annotations

import html
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings
from app.models.enums import NotificationStatus
from app.services.abonne_prefs import (
    abonne_has_active_preferences,
    abonne_preference_lists,
    offre_matches_keywords,
)
from app.services.email_delivery import send_html_email
from app.services.email_templates import MUTED, TEXT, email_offer_card, email_shell
from app.services.notification_interval import (
    notification_availability_label,
    notification_interval_label,
    notification_interval_minutes,
)
from app.services.offre_filters import (
    _normalize_oid_list,
    _oid_in,
    active_deadline_filter,
    merge_mongo_filters,
    offres_list_aggregation_pipeline,
    user_preferences_filter,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Envoie périodiquement les offres actives correspondant aux critères de chaque abonné."""

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
    def _lookback_minutes() -> int:
        return notification_interval_minutes()

    def _notification_sent_at_by_offre(
        self, db, abonne_id: ObjectId
    ) -> dict[ObjectId, datetime]:
        sent_at: dict[ObjectId, datetime] = {}
        for doc in db.notifications_envoyees.find(
            {"abonne_id": abonne_id},
            {"offre_id": 1, "date_envoi": 1},
        ):
            offre_id = doc.get("offre_id")
            date_envoi = doc.get("date_envoi")
            if not isinstance(offre_id, ObjectId) or not isinstance(date_envoi, datetime):
                continue
            previous = sent_at.get(offre_id)
            if previous is None or date_envoi > previous:
                sent_at[offre_id] = date_envoi
        return sent_at

    @staticmethod
    def _offre_matches_abonne_strict(
        offre: dict[str, Any],
        secteurs: list[Any],
        pays: list[str],
        abonne: dict[str, Any] | None = None,
    ) -> bool:
        """Même règles que GET /api/offres et GET /api/offres/{id}."""
        if pays and offre.get("pays") not in pays:
            return False
        if secteurs:
            secteur_id = offre.get("secteur_id")
            if secteur_id is None or not _oid_in(secteur_id, secteurs):
                return False
        if abonne is not None and not offre_matches_keywords(offre, abonne):
            return False
        return True

    def _secteur_names_map(self, db, secteur_ids: list[Any]) -> dict[str, str]:
        ids = _normalize_oid_list(secteur_ids)
        if not ids:
            return {}
        names: dict[str, str] = {}
        for doc in db.secteurs.find({"_id": {"$in": ids}}, {"nom": 1}):
            names[str(doc["_id"])] = doc.get("nom") or "Secteur"
        return names

    def _abonne_criteria_label(self, db, abonne: dict[str, Any]) -> str:
        secteurs, pays = abonne_preference_lists(abonne)
        secteur_map = self._secteur_names_map(db, secteurs)
        secteur_labels = [secteur_map.get(str(s), "Secteur") for s in secteurs]
        parts: list[str] = []
        if secteur_labels:
            parts.append(" · ".join(secteur_labels))
        if pays:
            parts.append(" · ".join(pays))
        return " · ".join(parts) if parts else "Vos critères Mon compte"

    @staticmethod
    def _normalize_titre(value: str | None) -> str:
        return " ".join((value or "").replace("\n", " ").split())

    def _enrich_offres_for_email(
        self,
        db,
        offres: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        secteur_ids = [
            o.get("secteur_id") for o in offres if o.get("secteur_id") is not None
        ]
        secteur_map = self._secteur_names_map(db, secteur_ids)
        enriched: list[dict[str, Any]] = []
        for offre in offres:
            copy = dict(offre)
            copy["titre"] = self._normalize_titre(copy.get("titre"))
            sid = copy.get("secteur_id")
            copy["secteur_nom"] = secteur_map.get(str(sid), "") if sid else ""
            enriched.append(copy)
        return enriched

    @staticmethod
    def _format_date(value: datetime | None) -> str:
        if not value:
            return "Non précisée"
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%d/%m/%Y")

    @staticmethod
    def _format_contact_lines(offre: dict[str, Any]) -> str:
        contact = offre.get("contact") if isinstance(offre.get("contact"), dict) else {}
        lines: list[str] = []
        mapping = (
            ("email", "Email"),
            ("telephone", "Téléphone"),
            ("telephone_responsable", "Tél. responsable"),
            ("responsable", "Responsable"),
            ("lieu_acquisition_dao", "Acquisition DAO"),
            ("lieu_depot", "Dépôt"),
        )
        for key, label in mapping:
            value = contact.get(key)
            if value:
                lines.append(f"{label} : {html.escape(str(value))}")
        return "<br>".join(lines)

    def _build_html_email(
        self,
        offres: list[dict[str, Any]],
        *,
        criteria_label: str,
        preview: bool = False,
    ) -> str:
        cards = []
        for offre in offres:
            contact_html = self._format_contact_lines(offre)
            cards.append(
                email_offer_card(
                    titre=offre.get("titre", ""),
                    organisme=offre.get("organisme", ""),
                    pays=offre.get("pays", ""),
                    secteur=offre.get("secteur_nom", ""),
                    date_limite=self._format_date(offre.get("date_limite")),
                    lien=offre.get("lien_source", "") or "",
                    contact_html=contact_html,
                )
            )

        count = len(offres)
        availability_label = notification_availability_label()
        safe_criteria = html.escape(criteria_label)
        preview_banner = (
            f"""<div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:10px;
            padding:12px 16px;margin-bottom:20px;font-size:14px;color:#92400e;">
            Aperçu — ces offres correspondent à vos critères actuels.</div>"""
            if preview
            else ""
        )
        if preview:
            intro = (
                f"<strong style=\"color:#047857;\">{count}</strong> offre(s) disponible(s) "
                f"(aperçu), {availability_label}."
            )
            eyebrow = "Aperçu alertes"
        else:
            intro = (
                f"<strong style=\"color:#047857;\">{count}</strong> offre(s) disponible(s), "
                f"{availability_label}."
            )
            eyebrow = "Offres disponibles"
        body = f"""
        {preview_banner}
        <p style="margin:0 0 6px;font-size:14px;color:{MUTED};">
          Votre sélection
        </p>
        <p style="margin:0 0 20px;font-size:16px;font-weight:700;color:{TEXT};">
          {safe_criteria}
        </p>
        <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:{TEXT};">
          {intro}
        </p>
        {''.join(cards)}
        """
        return email_shell(
            eyebrow=eyebrow,
            title=f"{count} opportunité{'s' if count > 1 else ''} pour vous",
            body_html=body,
            footer_note=f"Alertes automatiques {notification_interval_label()} — MarchéConnect",
        )

    @staticmethod
    def _recipient_emails(abonne: dict[str, Any]) -> list[str]:
        emails = [abonne["email"]]
        for extra in abonne.get("emails_supplementaires") or []:
            if extra and extra not in emails:
                emails.append(extra)
        return emails

    def _notified_offre_ids(self, db, abonne_id: ObjectId) -> set[ObjectId]:
        ids = db.notifications_envoyees.distinct("offre_id", {"abonne_id": abonne_id})
        return {oid for oid in ids if isinstance(oid, ObjectId)}

    def _fetch_active_offres_for_abonne(
        self,
        db,
        abonne: dict[str, Any],
        *,
        max_offres: int | None = None,
    ) -> list[dict[str, Any]]:
        """Offres actives (date limite non dépassée) correspondant aux préférences."""
        secteurs, pays = abonne_preference_lists(abonne)
        query = merge_mongo_filters(
            active_deadline_filter(),
            user_preferences_filter(secteurs, pays),
        )
        pipeline = offres_list_aggregation_pipeline(
            query,
            limit=max_offres,
        )
        offres = list(db.offres.aggregate(pipeline))
        filtered = [
            offre
            for offre in offres
            if self._offre_matches_abonne_strict(offre, secteurs, pays, abonne)
        ]
        if max_offres is not None:
            filtered = filtered[: max(1, max_offres)]
        return self._enrich_offres_for_email(db, filtered)

    def _pick_offres_for_scheduled_send(
        self,
        db,
        abonne: dict[str, Any],
        abonne_id: ObjectId,
        already_notified: set[ObjectId],
        *,
        max_offres: int,
    ) -> list[dict[str, Any]]:
        """Sélectionne les offres à envoyer : d'abord non encore notifiées, puis rotation."""
        active = self._fetch_active_offres_for_abonne(db, abonne)
        if not active:
            return []

        limit = max(1, max_offres)
        unnotified = [offre for offre in active if offre["_id"] not in already_notified]
        if unnotified:
            return unnotified[:limit]

        sent_at = self._notification_sent_at_by_offre(db, abonne_id)
        epoch = datetime.min.replace(tzinfo=timezone.utc)
        rotated = sorted(active, key=lambda offre: sent_at.get(offre["_id"], epoch))
        return rotated[:limit]

    def send_to_abonne(
        self,
        abonne: dict[str, Any],
        *,
        preview: bool = False,
    ) -> dict[str, Any]:
        """Envoie un digest personnalisé à un abonné (aperçu ou alerte planifiée)."""
        if not abonne_has_active_preferences(abonne):
            return {
                "statut": NotificationStatus.SUCCES.value,
                "nb_emails_envoyes": 0,
                "nb_echecs": 0,
                "nb_offres": 0,
                "message_erreur": "Préférences secteurs/pays non configurées",
            }

        db = self._get_db()
        abonne_id = abonne["_id"]
        max_offres = None if preview else settings.notification_max_offres_per_email

        if preview:
            matching = self._fetch_active_offres_for_abonne(db, abonne)
        else:
            already_notified = self._notified_offre_ids(db, abonne_id)
            matching = self._pick_offres_for_scheduled_send(
                db,
                abonne,
                abonne_id,
                already_notified,
                max_offres=max_offres or settings.notification_max_offres_per_email,
            )
        criteria_label = self._abonne_criteria_label(db, abonne)

        if not matching:
            logger.info(
                "Aucune offre active à envoyer pour %s",
                abonne.get("email"),
            )
            return {
                "statut": NotificationStatus.SUCCES.value,
                "nb_emails_envoyes": 0,
                "nb_echecs": 0,
                "nb_offres": 0,
                "message_erreur": None,
            }

        subject_prefix = "Aperçu" if preview else "Offres disponibles"
        subject = f"[MarchéConnect] {subject_prefix} — {len(matching)} offre(s)"
        html_body = self._build_html_email(
            matching,
            criteria_label=criteria_label,
            preview=preview,
        )
        offre_ids = [offre["_id"] for offre in matching]
        nb_envoyes = 0
        nb_echecs = 0
        erreurs: list[str] = []
        sent = False

        for addr in self._recipient_emails(abonne):
            try:
                send_html_email(addr, subject, html_body)
                nb_envoyes += 1
                sent = True
            except Exception as exc:
                nb_echecs += 1
                erreurs.append(f"{addr}: {exc}")

        if sent and not preview:
            self._mark_offres_notified(db, abonne_id, offre_ids)
            db.abonnes.update_one(
                {"_id": abonne_id},
                {"$set": {"last_notification_at": datetime.now(timezone.utc)}},
            )

        if nb_echecs and nb_envoyes:
            statut = NotificationStatus.PARTIEL
        elif nb_echecs:
            statut = NotificationStatus.ECHEC
        else:
            statut = NotificationStatus.SUCCES

        return {
            "statut": statut.value,
            "nb_emails_envoyes": nb_envoyes,
            "nb_echecs": nb_echecs,
            "nb_offres": len(matching),
            "message_erreur": "; ".join(erreurs[:3]) if erreurs else None,
        }

    def _mark_offres_notified(
        self,
        db,
        abonne_id: ObjectId,
        offre_ids: list[ObjectId],
    ) -> None:
        if not offre_ids:
            return
        now = datetime.now(timezone.utc)
        docs = [
            {"abonne_id": abonne_id, "offre_id": offre_id, "date_envoi": now}
            for offre_id in offre_ids
        ]
        try:
            db.notifications_envoyees.insert_many(docs, ordered=False)
        except BulkWriteError as exc:
            if exc.details.get("writeErrors"):
                non_dup = [
                    err
                    for err in exc.details["writeErrors"]
                    if err.get("code") != 11000
                ]
                if non_dup:
                    raise

    def _log_execution(
        self,
        statut: NotificationStatus,
        nb_envoyes: int,
        nb_echecs: int,
        nb_abonnes_traites: int,
        message_erreur: str | None = None,
    ) -> None:
        self._get_db().logs_notifications.insert_one(
            {
                "date_execution": datetime.now(timezone.utc),
                "statut": statut.value,
                "nb_emails_envoyes": nb_envoyes,
                "nb_echecs": nb_echecs,
                "nb_abonnes_traites": nb_abonnes_traites,
                "intervalle_minutes": self._lookback_minutes(),
                "message_erreur": message_erreur,
            }
        )

    def _get_eligible_abonnes(self, db) -> list[dict[str, Any]]:
        candidates = list(
            db.abonnes.find(
                {
                    "actif": True,
                    "utilisateur_id": {"$exists": True, "$ne": None},
                }
            )
        )
        eligible: list[dict[str, Any]] = []
        for abonne in candidates:
            if not abonne_has_active_preferences(abonne):
                continue
            utilisateur_id = abonne.get("utilisateur_id")
            if not isinstance(utilisateur_id, ObjectId):
                continue
            if db.utilisateurs.count_documents({"_id": utilisateur_id}, limit=1) == 0:
                continue
            eligible.append(abonne)
        return eligible

    def run(self) -> dict[str, Any]:
        nb_envoyes = 0
        nb_echecs = 0
        nb_abonnes_traites = 0
        erreurs: list[str] = []

        try:
            db = self._get_db()
            abonnes = self._get_eligible_abonnes(db)

            logger.info(
                "Alertes email : %d abonné(s) éligible(s)",
                len(abonnes),
            )

            if not abonnes:
                statut = NotificationStatus.SUCCES
                self._log_execution(statut, 0, 0, 0, None)
                return {
                    "statut": statut.value,
                    "nb_emails_envoyes": 0,
                    "nb_echecs": 0,
                    "nb_offres_recentes": 0,
                    "nb_abonnes_traites": 0,
                    "message_erreur": None,
                }

            total_offres_vues = 0

            for abonne in abonnes:
                nb_abonnes_traites += 1
                result = self.send_to_abonne(abonne, preview=False)
                total_offres_vues += result.get("nb_offres", 0)
                nb_envoyes += result.get("nb_emails_envoyes", 0)
                nb_echecs += result.get("nb_echecs", 0)
                if result.get("message_erreur"):
                    erreurs.append(str(result["message_erreur"]))
                if result.get("nb_offres", 0) == 0:
                    logger.info(
                        "Aucune offre à envoyer pour %s",
                        abonne["email"],
                    )
                else:
                    logger.info(
                        "Alerte %s : %d offre(s), %d email(s)",
                        abonne["email"],
                        result.get("nb_offres", 0),
                        result.get("nb_emails_envoyes", 0),
                    )

            if nb_echecs and nb_envoyes:
                statut = NotificationStatus.PARTIEL
            elif nb_echecs:
                statut = NotificationStatus.ECHEC
            else:
                statut = NotificationStatus.SUCCES

            message = "; ".join(erreurs[:5]) if erreurs else None
            if erreurs and len(erreurs) > 5:
                message += f" (+{len(erreurs) - 5} autre(s) erreur(s))"

            self._log_execution(
                statut, nb_envoyes, nb_echecs, nb_abonnes_traites, message
            )
            return {
                "statut": statut.value,
                "nb_emails_envoyes": nb_envoyes,
                "nb_echecs": nb_echecs,
                "nb_offres_recentes": total_offres_vues,
                "nb_abonnes_traites": nb_abonnes_traites,
                "message_erreur": message,
            }

        except Exception as exc:
            msg = f"Erreur notification ({type(exc).__name__}) : {exc}"
            logger.error(msg, exc_info=True)
            self._log_execution(
                NotificationStatus.ECHEC, nb_envoyes, nb_echecs, nb_abonnes_traites, msg
            )
            return {
                "statut": NotificationStatus.ECHEC.value,
                "nb_emails_envoyes": nb_envoyes,
                "nb_echecs": nb_echecs,
                "nb_offres_recentes": 0,
                "nb_abonnes_traites": nb_abonnes_traites,
                "message_erreur": msg,
            }

        finally:
            self.close()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    result = NotificationService().run()
    print(
        f"Statut           : {result['statut']}\n"
        f"Abonnés traités  : {result['nb_abonnes_traites']}\n"
        f"Offres filtrées  : {result['nb_offres_recentes']}\n"
        f"Emails envoyés   : {result['nb_emails_envoyes']}\n"
        f"Échecs           : {result['nb_echecs']}"
    )
    if result["message_erreur"]:
        print(f"Erreur           : {result['message_erreur']}")
    return 0 if result["statut"] != NotificationStatus.ECHEC.value else 1


if __name__ == "__main__":
    sys.exit(main())
