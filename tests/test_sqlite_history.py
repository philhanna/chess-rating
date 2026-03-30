import json
import sqlite3

from rating.adapters.sqlite_history import SQLiteHistoryAdapter
from rating.domain.models import (
    NormalizedRatingProfile,
    PlayerIdentity,
    RatingMetadata,
    build_ratings,
)


def test_save_creates_schema_and_inserts_profile(tmp_path):
    database_path = tmp_path / "history.sqlite3"
    adapter = SQLiteHistoryAdapter(str(database_path))
    profile = NormalizedRatingProfile(
        provider="lichess",
        player=PlayerIdentity(id="pehanna", display_name="pehanna"),
        ratings=build_ratings(standard=1800, blitz=1700),
        extras={"puzzle": 2200},
        metadata=RatingMetadata(as_of="2026-03-30", source_url="https://example.com/profile"),
    )

    adapter.save(profile)

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT provider, player_id, display_name, standard, blitz, extras_json, as_of, source_url
            FROM rating_history
            """
        ).fetchone()

    assert row == (
        "lichess",
        "pehanna",
        "pehanna",
        1800,
        1700,
        json.dumps({"puzzle": 2200}, sort_keys=True),
        "2026-03-30",
        "https://example.com/profile",
    )


def test_save_stores_provider_specific_rows_in_one_table(tmp_path):
    database_path = tmp_path / "history.sqlite3"
    adapter = SQLiteHistoryAdapter(str(database_path))

    adapter.save(
        NormalizedRatingProfile(
            provider="uscf",
            player=PlayerIdentity(id="1", display_name="One"),
            ratings=build_ratings(standard=1500),
        )
    )
    adapter.save(
        NormalizedRatingProfile(
            provider="fide",
            player=PlayerIdentity(id="2", display_name="Two"),
            ratings=build_ratings(standard=2000),
        )
    )

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT provider, player_id FROM rating_history ORDER BY player_id"
        ).fetchall()

    assert rows == [("uscf", "1"), ("fide", "2")]
