"""Classification automatique des offres par secteur (mots-clés)."""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.db.config import settings

logger = logging.getLogger(__name__)


class SectorClassificationService:
    """Assigne un secteur aux offres non classées via correspondance de mots-clés."""

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
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower())

    @staticmethod
    def _count_keyword_matches(text: str, keywords: list[str]) -> int:
        count = 0
        for keyword in keywords:
            kw = keyword.strip().lower()
            if kw and kw in text:
                count += 1
        return count

    def classify_text(
        self, titre: str, description: str, secteurs: list[dict[str, Any]]
    ) -> Any | None:
        text = self._normalize(f"{titre} {description}")
        scores: dict[Any, int] = {}

        for secteur in secteurs:
            matches = self._count_keyword_matches(text, secteur.get("mots_cles", []))
            if matches > 0:
                scores[secteur["_id"]] = matches

        if not scores:
            return None

        best_score = max(scores.values())
        winners = [sid for sid, score in scores.items() if score == best_score]

        if len(winners) > 1:
            return None

        return winners[0]

    def run(self) -> dict[str, int]:
        db = self._get_db()
        secteurs = list(db.secteurs.find())
        offres = list(db.offres.find({"secteur_id": None}))

        classified = 0
        skipped = 0

        for offre in offres:
            secteur_id = self.classify_text(
                offre.get("titre", ""),
                offre.get("description", ""),
                secteurs,
            )
            if secteur_id is None:
                skipped += 1
                continue

            db.offres.update_one(
                {"_id": offre["_id"]},
                {"$set": {"secteur_id": secteur_id}},
            )
            classified += 1

        logger.info(
            "Classification terminée : %d classée(s), %d sans match clair, %d traitée(s)",
            classified,
            skipped,
            len(offres),
        )
        return {
            "total_traitees": len(offres),
            "classifiees": classified,
            "sans_match": skipped,
        }


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    service = SectorClassificationService()
    try:
        result = service.run()
        print(
            f"Offres traitées  : {result['total_traitees']}\n"
            f"Classifiées      : {result['classifiees']}\n"
            f"Sans match clair : {result['sans_match']}"
        )
        return 0
    finally:
        service.close()


if __name__ == "__main__":
    sys.exit(main())
