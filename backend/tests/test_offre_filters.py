"""Tests des filtres MongoDB partagés pour les offres."""

from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app.services.offre_filters import (
    active_deadline_filter,
    merge_mongo_filters,
    user_preferences_filter,
)


def test_active_deadline_includes_future_and_null():
    filt = active_deadline_filter()
    assert "$or" in filt


def test_user_preferences_filter_sector_and_country():
    secteur_id = ObjectId()
    filt = user_preferences_filter([secteur_id], ["Bénin"])
    assert filt == {
        "$and": [
            {"secteur_id": {"$in": [secteur_id]}},
            {"pays": {"$in": ["Bénin"]}},
        ]
    }


def test_merge_mongo_filters_combines_clauses():
    now = datetime.now(timezone.utc)
    merged = merge_mongo_filters(
        {"date_scraping": {"$gte": now - timedelta(days=1)}},
        user_preferences_filter([], ["Bénin"]),
    )
    assert "$and" in merged
    assert len(merged["$and"]) == 2
