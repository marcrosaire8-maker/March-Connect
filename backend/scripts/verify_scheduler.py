"""Vérifie que APScheduler déclenche bien les jobs."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

RUN_COUNT = 0


def sample_job() -> None:
    global RUN_COUNT
    RUN_COUNT += 1
    logging.getLogger(__name__).info("Job scheduler exécuté (run #%d)", RUN_COUNT)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        sample_job,
        trigger=IntervalTrigger(seconds=2),
        id="test_job",
    )
    scheduler.start()
    logging.info("Scheduler démarré — attente de 2 exécutions...")
    time.sleep(5.5)
    scheduler.shutdown(wait=False)

    if RUN_COUNT >= 2:
        print(f"✅ Scheduler OK : {RUN_COUNT} exécution(s) détectée(s)")
        return 0

    print(f"❌ Scheduler KO : seulement {RUN_COUNT} exécution(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
