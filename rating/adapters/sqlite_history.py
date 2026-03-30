"""SQLite persistence adapter for rating history."""

import json
import os
import sqlite3
from datetime import datetime, timezone

from rating.domain.models import NormalizedRatingProfile
from rating.ports.history_port import HistoryPort


class SQLiteHistoryAdapter(HistoryPort):
    """Store normalized rating profiles in an SQLite database."""

    def __init__(self, database_path: str):
        self.database_path = database_path

    def save(self, profile: NormalizedRatingProfile) -> None:
        """Create the schema if needed and insert one history row."""
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            self._create_schema(connection)
            connection.execute(
                """
                INSERT INTO rating_history (
                    recorded_at,
                    provider,
                    player_id,
                    display_name,
                    standard,
                    rapid,
                    blitz,
                    bullet,
                    correspondence,
                    extras_json,
                    as_of,
                    source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    profile.provider,
                    profile.player.id,
                    profile.player.display_name,
                    profile.ratings.get("standard"),
                    profile.ratings.get("rapid"),
                    profile.ratings.get("blitz"),
                    profile.ratings.get("bullet"),
                    profile.ratings.get("correspondence"),
                    json.dumps(profile.extras, sort_keys=True),
                    profile.metadata.as_of,
                    profile.metadata.source_url,
                ),
            )
            connection.commit()

    def _create_schema(self, connection: sqlite3.Connection) -> None:
        """Ensure the history table exists before inserts."""
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS rating_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                provider TEXT NOT NULL,
                player_id TEXT NOT NULL,
                display_name TEXT,
                standard INTEGER,
                rapid INTEGER,
                blitz INTEGER,
                bullet INTEGER,
                correspondence INTEGER,
                extras_json TEXT NOT NULL,
                as_of TEXT,
                source_url TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_rating_history_provider_player_recorded
            ON rating_history (provider, player_id, recorded_at)
            """
        )
