"""Planification automatique : collecte → classification → alertes email."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.config import settings
from app.scrapers.registry import run_all_scrapers
from app.services.classification import SectorClassificationService
from app.services.deadline_reminders import DeadlineReminderService
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_classification() -> dict[str, int]:
    logger.info("Job planifié — classification sectorielle")
    service = SectorClassificationService()
    try:
        stats = service.run()
        logger.info(
            "  Classification : %d/%d classées",
            stats["classifiees"],
            stats["total_traitees"],
        )
        return stats
    finally:
        service.close()


def _notifications_job() -> None:
    logger.info("Job planifié — envoi des notifications email")
    try:
        result = NotificationService().run()
        logger.info(
            "  Notifications : %s (%d envoyé(s), %d échec(s), %d offre(s) récente(s))",
            result["statut"],
            result["nb_emails_envoyes"],
            result["nb_echecs"],
            result["nb_offres_recentes"],
        )
    except Exception as exc:
        logger.error("Erreur notifications : %s", exc, exc_info=True)


def _deadline_reminders_job() -> None:
    logger.info("Job planifié — rappels d'échéance")
    try:
        result = DeadlineReminderService().run()
        logger.info(
            "  Rappels : %d envoyé(s), %d échec(s)",
            result.get("envoyes", 0),
            result.get("echecs", 0),
        )
    except Exception as exc:
        logger.error("Erreur rappels échéance : %s", exc, exc_info=True)


def _scrape_and_classify_job() -> None:
    """Collecte les offres, les classe, puis déclenche les alertes clients."""
    logger.info("Job planifié — démarrage des scrapers")
    try:
        results = run_all_scrapers()
        for result in results:
            logger.info(
                "  %s : %s (%d trouvées, %d nouvelles)",
                result["source"],
                result.get("statut", "inconnu"),
                result.get("nb_offres_trouvees", 0),
                result.get("nb_offres_nouvelles", 0),
            )
    except Exception as exc:
        logger.error("Erreur scrapers : %s", exc, exc_info=True)

    try:
        _run_classification()
    except Exception as exc:
        logger.error("Erreur classification : %s", exc, exc_info=True)

    _notifications_job()


def _add_scrape_job(scheduler: BackgroundScheduler, *, interval_minutes: int) -> None:
    tz = ZoneInfo(settings.scheduler_timezone)
    kwargs: dict = {
        "trigger": IntervalTrigger(minutes=max(1, interval_minutes)),
        "id": "scraping_interval",
        "replace_existing": True,
        "max_instances": 1,
        "coalesce": True,
    }
    if settings.automation_startup_run:
        kwargs["next_run_time"] = datetime.now(tz)
    scheduler.add_job(_scrape_and_classify_job, **kwargs)


def _add_notifications_job(scheduler: BackgroundScheduler, *, interval_minutes: int) -> None:
    scheduler.add_job(
        _notifications_job,
        trigger=IntervalTrigger(minutes=max(1, interval_minutes)),
        id="notifications_interval",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _deadline_reminders_job,
        trigger=IntervalTrigger(hours=6),
        id="deadline_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    tz = ZoneInfo(settings.scheduler_timezone)
    _scheduler = BackgroundScheduler(timezone=tz)

    if settings.scheduler_test_interval_seconds > 0:
        test_seconds = settings.scheduler_test_interval_seconds
        logger.warning("Mode test scheduler : intervalle de %ds", test_seconds)
        _scheduler.add_job(
            _scrape_and_classify_job,
            trigger=IntervalTrigger(seconds=test_seconds),
            id="scraping_interval",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            next_run_time=datetime.now(tz) if settings.automation_startup_run else None,
        )
        _scheduler.add_job(
            _notifications_job,
            trigger=IntervalTrigger(seconds=test_seconds),
            id="notifications_interval",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        logger.info(
            "Scheduler test : collecte+alertes toutes les %ds (%s)",
            test_seconds,
            settings.scheduler_timezone,
        )
    else:
        scrape_minutes = max(1, settings.scrape_interval_minutes)
        notify_minutes = max(1, settings.notification_interval_minutes)
        _add_scrape_job(_scheduler, interval_minutes=scrape_minutes)
        _add_notifications_job(_scheduler, interval_minutes=notify_minutes)
        logger.info(
            "Robot autonome actif : collecte toutes les %d min, "
            "alertes email toutes les %d min (%s)",
            scrape_minutes,
            notify_minutes,
            settings.scheduler_timezone,
        )
        if settings.automation_startup_run:
            logger.info("Première collecte programmée au démarrage")

    _scheduler.start()
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler arrêté")


def get_scheduler() -> BackgroundScheduler | None:
    return _scheduler
