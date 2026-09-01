"""SQLite implementation of the profile logging port."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from rating.domain.models import NormalizedRatingProfile
from rating.ports.profile_log_port import ProfileLogPort


class SQLiteProfileLogAdapter(ProfileLogPort):
    """Persist rating profiles as normalized, immutable snapshots."""

    def __init__(self, database_path: Union[str, Path]):
        self.database_path = Path(database_path).expanduser()

    def log(self, profile: NormalizedRatingProfile) -> None:
        """Write one profile snapshot, creating its database and schema as needed.

        Skips writing if the ratings match the player's most recent snapshot.
        """
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.database_path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            self._create_schema(connection)

            provider_id = self._get_or_create_provider(connection, profile.provider)
            player_id = self._get_or_create_player(
                connection,
                provider_id,
                profile.player.id,
            )

            new_ratings = {**profile.ratings, **profile.extras}
            if self._latest_ratings(connection, player_id) == new_ratings:
                return

            snapshot_id = connection.execute(
                """
                INSERT INTO profile_snapshots
                    (player_id, display_name, as_of, source_url)
                VALUES (?, ?, ?, ?)
                """,
                (
                    player_id,
                    profile.player.display_name,
                    profile.metadata.as_of,
                    profile.metadata.source_url,
                ),
            ).lastrowid

            for name, value in profile.ratings.items():
                category_id = self._get_or_create_category(connection, name, True)
                self._insert_rating(connection, snapshot_id, category_id, value)

            for name, value in profile.extras.items():
                category_id = self._get_or_create_category(connection, name, False)
                self._insert_rating(connection, snapshot_id, category_id, value)

    def history(
        self, provider: str, external_id: str, category: str
    ) -> List[Tuple[Optional[str], Optional[int]]]:
        """Return a player's ``(when, value)`` pairs for one rating category.

        ``when`` is the provider-reported ``as_of`` date if available, else the
        timestamp this app logged the snapshot. Rows are ordered oldest to
        newest by snapshot. Returns an empty list if the database, player, or
        category doesn't exist.
        """
        if not self.database_path.exists():
            return []

        with sqlite3.connect(str(self.database_path)) as connection:
            rows = connection.execute(
                """
                SELECT COALESCE(s.as_of, s.logged_at), v.value
                FROM profile_snapshots AS s
                JOIN players AS pl ON pl.id = s.player_id
                JOIN providers AS pr ON pr.id = pl.provider_id
                JOIN rating_values AS v ON v.snapshot_id = s.id
                JOIN rating_categories AS c ON c.id = v.category_id
                WHERE pr.name = ? AND pl.external_id = ? AND c.name = ?
                ORDER BY s.id
                """,
                (provider, external_id, category),
            ).fetchall()
        return rows

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                provider_id INTEGER NOT NULL REFERENCES providers(id),
                external_id TEXT NOT NULL,
                UNIQUE (provider_id, external_id)
            );

            CREATE TABLE IF NOT EXISTS rating_categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                is_canonical INTEGER NOT NULL
                    CHECK (is_canonical IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS profile_snapshots (
                id INTEGER PRIMARY KEY,
                player_id INTEGER NOT NULL REFERENCES players(id),
                display_name TEXT,
                as_of TEXT,
                source_url TEXT,
                logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rating_values (
                snapshot_id INTEGER NOT NULL
                    REFERENCES profile_snapshots(id) ON DELETE CASCADE,
                category_id INTEGER NOT NULL REFERENCES rating_categories(id),
                value INTEGER,
                PRIMARY KEY (snapshot_id, category_id)
            );

            CREATE INDEX IF NOT EXISTS profile_snapshots_player_id_idx
                ON profile_snapshots(player_id);
            """
        )

    @staticmethod
    def _get_or_create_provider(
        connection: sqlite3.Connection, provider: str
    ) -> int:
        connection.execute(
            "INSERT OR IGNORE INTO providers (name) VALUES (?)",
            (provider,),
        )
        row = connection.execute(
            "SELECT id FROM providers WHERE name = ?",
            (provider,),
        ).fetchone()
        assert row is not None
        return row[0]

    @staticmethod
    def _get_or_create_player(
        connection: sqlite3.Connection,
        provider_id: int,
        external_id: str,
    ) -> int:
        connection.execute(
            """
            INSERT OR IGNORE INTO players (provider_id, external_id)
            VALUES (?, ?)
            """,
            (provider_id, external_id),
        )
        row = connection.execute(
            """
            SELECT id
            FROM players
            WHERE provider_id = ? AND external_id = ?
            """,
            (provider_id, external_id),
        ).fetchone()
        assert row is not None
        return row[0]

    @staticmethod
    def _latest_ratings(
        connection: sqlite3.Connection, player_id: int
    ) -> Optional[Dict[str, Optional[int]]]:
        snapshot_row = connection.execute(
            """
            SELECT id
            FROM profile_snapshots
            WHERE player_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (player_id,),
        ).fetchone()
        if snapshot_row is None:
            return None

        rows = connection.execute(
            """
            SELECT c.name, v.value
            FROM rating_values AS v
            JOIN rating_categories AS c ON c.id = v.category_id
            WHERE v.snapshot_id = ?
            """,
            (snapshot_row[0],),
        ).fetchall()
        return dict(rows)

    @staticmethod
    def _get_or_create_category(
        connection: sqlite3.Connection, name: str, is_canonical: bool
    ) -> int:
        connection.execute(
            """
            INSERT INTO rating_categories (name, is_canonical)
            VALUES (?, ?)
            ON CONFLICT (name) DO NOTHING
            """,
            (name, int(is_canonical)),
        )
        row = connection.execute(
            """
            SELECT id, is_canonical
            FROM rating_categories
            WHERE name = ?
            """,
            (name,),
        ).fetchone()
        assert row is not None
        if row[1] != int(is_canonical):
            raise ValueError(
                'Rating category "{}" cannot be both canonical and extra'.format(name)
            )
        return row[0]

    @staticmethod
    def _insert_rating(
        connection: sqlite3.Connection,
        snapshot_id: int,
        category_id: int,
        value: Optional[int],
    ) -> None:
        connection.execute(
            """
            INSERT INTO rating_values (snapshot_id, category_id, value)
            VALUES (?, ?, ?)
            """,
            (snapshot_id, category_id, value),
        )
