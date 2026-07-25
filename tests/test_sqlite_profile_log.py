import sqlite3
from pathlib import Path

from rating.adapters.sqlite_profile_log import SQLiteProfileLogAdapter
from rating.application.rating import log_profile
from rating.domain.models import (
    NormalizedRatingProfile,
    PlayerIdentity,
    RatingMetadata,
    build_ratings,
)


def _profile(display_name="Player One", standard=1500):
    return NormalizedRatingProfile(
        provider="lichess",
        player=PlayerIdentity(id="player1", display_name=display_name),
        ratings=build_ratings(standard=standard, blitz=1400),
        extras={"puzzle": 2000},
        metadata=RatingMetadata(
            as_of="2026-03-30",
            source_url="https://example.com/player1",
        ),
    )


def _rows(database, sql):
    with sqlite3.connect(str(database)) as connection:
        return connection.execute(sql).fetchall()


def test_log_profile_delegates_to_profile_log_port():
    received = []

    class FakeProfileLog:
        def log(self, profile):
            received.append(profile)

    profile = _profile()
    log_profile(profile, FakeProfileLog())

    assert received == [profile]


def test_sqlite_adapter_creates_database_and_normalized_profile(tmp_path):
    database = tmp_path / "nested" / "ratings.db"

    SQLiteProfileLogAdapter(database).log(_profile())

    assert database.is_file()
    assert _rows(database, "SELECT name FROM providers") == [("lichess",)]
    assert _rows(database, "SELECT external_id FROM players") == [("player1",)]
    assert _rows(
        database,
        """
        SELECT display_name, as_of, source_url
        FROM profile_snapshots
        """,
    ) == [
        (
            "Player One",
            "2026-03-30",
            "https://example.com/player1",
        )
    ]

    categories = dict(
        _rows(
            database,
            "SELECT name, is_canonical FROM rating_categories",
        )
    )
    assert categories == {
        "standard": 1,
        "rapid": 1,
        "blitz": 1,
        "bullet": 1,
        "correspondence": 1,
        "puzzle": 0,
    }
    assert _rows(
        database,
        """
        SELECT c.name, v.value
        FROM rating_values AS v
        JOIN rating_categories AS c ON c.id = v.category_id
        ORDER BY c.name
        """,
    ) == [
        ("blitz", 1400),
        ("bullet", None),
        ("correspondence", None),
        ("puzzle", 2000),
        ("rapid", None),
        ("standard", 1500),
    ]


def test_repeated_logs_reuse_dimensions_and_create_new_snapshots(tmp_path):
    database = tmp_path / "ratings.db"
    adapter = SQLiteProfileLogAdapter(database)

    adapter.log(_profile("Old Name", standard=1500))
    adapter.log(_profile("New Name", standard=1510))

    assert _rows(database, "SELECT COUNT(*) FROM providers") == [(1,)]
    assert _rows(database, "SELECT COUNT(*) FROM players") == [(1,)]
    assert _rows(database, "SELECT COUNT(*) FROM rating_categories") == [(6,)]
    assert _rows(database, "SELECT COUNT(*) FROM profile_snapshots") == [(2,)]
    assert _rows(database, "SELECT COUNT(*) FROM rating_values") == [(12,)]
    assert _rows(
        database,
        "SELECT display_name FROM profile_snapshots ORDER BY id",
    ) == [("Old Name",), ("New Name",)]


def test_repeated_logs_skip_when_ratings_unchanged(tmp_path):
    database = tmp_path / "ratings.db"
    adapter = SQLiteProfileLogAdapter(database)

    adapter.log(_profile("Old Name"))
    adapter.log(_profile("New Name"))

    assert _rows(database, "SELECT COUNT(*) FROM profile_snapshots") == [(1,)]
    assert _rows(
        database,
        "SELECT display_name FROM profile_snapshots",
    ) == [("Old Name",)]


def test_default_database_path_is_under_home_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    adapter = SQLiteProfileLogAdapter()
    adapter.log(_profile())

    assert adapter.database_path == (
        tmp_path / ".cache" / "chess-rating" / "ratings.db"
    )
    assert adapter.database_path.is_file()
