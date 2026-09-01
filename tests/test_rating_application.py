import json
from pathlib import Path

import pytest

from rating.application import rating
from rating.domain.models import (
    NormalizedRatingProfile,
    PlayerIdentity,
    RatingMetadata,
    build_ratings,
)


@pytest.fixture(autouse=True)
def _disable_profile_logging_from_cli_tests(monkeypatch):
    """Keep CLI unit tests from writing to the user's real cache directory."""
    logged_profiles = []
    monkeypatch.setattr(
        rating,
        "log_profile",
        lambda profile, database_path: logged_profiles.append((profile, database_path)),
    )
    return logged_profiles


@pytest.fixture(autouse=True)
def _no_graph_popups_in_tests(monkeypatch):
    """Keep history-graph tests from blocking on a real GUI window."""
    import matplotlib.pyplot as plt

    monkeypatch.setattr(rating, "_show_graph", lambda fig, *args, **kwargs: plt.close(fig))


def _make_profile(
    provider="uscf",
    player_id="player1",
    display_name="Player One",
    ratings=None,
):
    if ratings is None:
        ratings = build_ratings(standard=1500, blitz=1400)
    return NormalizedRatingProfile(
        provider=provider,
        player=PlayerIdentity(id=player_id, display_name=display_name),
        ratings=ratings,
        extras={"puzzle": 2000},
        metadata=RatingMetadata(as_of="2026-03-30", source_url="https://example.com/profile"),
    )


def test_format_rating_value_handles_none_and_numbers():
    assert rating._format_rating_value(None) == "Not rated"
    assert rating._format_rating_value(1500) == "1500"


def test_to_json_serializes_normalized_profile():
    profile = _make_profile(provider="lichess", player_id="pehanna", display_name="pehanna")

    payload = json.loads(rating._to_json(profile))

    assert payload["provider"] == "lichess"
    assert payload["player"]["id"] == "pehanna"
    assert payload["player"]["display_name"] == "pehanna"
    assert payload["ratings"]["standard"] == 1500
    assert payload["extras"]["puzzle"] == 2000
    assert payload["metadata"]["as_of"] == "2026-03-30"


def test_to_pipe_renders_canonical_fields_extras_and_as_of():
    profile = _make_profile()

    result = rating._to_pipe(profile)

    assert "|" not in result
    assert "\n" in result
    assert "provider=uscf" in result
    assert "player_id=player1" in result
    assert "display_name=Player One" in result
    assert "standard=1500" in result
    assert "rapid=" not in result
    assert "blitz=1400" in result
    assert "puzzle=2000" in result
    assert "as_of=2026-03-30" in result
    assert "source_url=" not in result


def test_to_pipe_verbose_includes_source_url():
    profile = _make_profile()

    result = rating._to_pipe(profile, verbose=True)

    assert "source_url=https://example.com/profile" in result


class _FakeLoader:
    filename = str(Path(".env"))
    config_overrides = {}

    def __init__(self, *_args, **_kwargs):
        self.filename = self.__class__.filename
        self.config = {
            "DBFILE": "/configured/ratings.db",
            "USCF": {"defaultUser": "uscf-default"},
            "lichess": {"defaultUser": "lichess-default"},
            "Chess": {"defaultUser": "chess-default"},
            "FIDE": {"defaultUser": "fide-default"},
        }
        self.config.update(self.__class__.config_overrides)

    @classmethod
    def reset(cls):
        cls.filename = str(Path(".env"))
        cls.config_overrides = {}


class _FakeHttpClient:
    pass


def test_main_requires_a_platform_selection(monkeypatch, capsys):
    _FakeLoader.reset()

    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating"])

    with pytest.raises(SystemExit) as exc_info:
        rating.main()

    assert exc_info.value.code == 2
    assert "one of the arguments -u/--uscf -l/--lichess -c/--chess -f/--fide is required" in capsys.readouterr().err


def test_main_selects_uscf_and_uses_plain_output(
    monkeypatch, capsys, _disable_profile_logging_from_cli_tests
):
    created = {}
    profile = _make_profile(provider="uscf", player_id="uscf-default", display_name="uscf-default")
    _FakeLoader.reset()

    class FakeUSCF:
        def __init__(self, player, http_client):
            created["player"] = player
            created["http_client"] = http_client

        def fetch(self):
            return profile

        def getPrimaryRatingKey(self):
            return "standard"

    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(rating, "RequestsHttpAdapter", _FakeHttpClient)
    monkeypatch.setattr(rating, "USCF", FakeUSCF)
    monkeypatch.setattr(rating, "Lichess", object)
    monkeypatch.setattr(rating, "ChessCom", object)
    monkeypatch.setattr(rating, "FIDE", object)
    monkeypatch.setattr("sys.argv", ["rating", "--uscf"])

    rating.main()

    output = capsys.readouterr().out.strip()
    assert created["player"] == "uscf-default"
    assert isinstance(created["http_client"], _FakeHttpClient)
    assert _disable_profile_logging_from_cli_tests == [
        (profile, "/configured/ratings.db")
    ]
    assert output == "1500"


def test_main_uscf_verbose_renders_full_pipe(monkeypatch, capsys):
    profile = _make_profile(provider="uscf", player_id="uscf-default", display_name="uscf-default")
    _FakeLoader.reset()

    class FakeUSCF:
        def __init__(self, player, http_client):
            pass

        def fetch(self):
            return profile

        def getPrimaryRatingKey(self):
            return "standard"

    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(rating, "RequestsHttpAdapter", _FakeHttpClient)
    monkeypatch.setattr(rating, "USCF", FakeUSCF)
    monkeypatch.setattr(rating, "Lichess", object)
    monkeypatch.setattr(rating, "ChessCom", object)
    monkeypatch.setattr(rating, "FIDE", object)
    monkeypatch.setattr("sys.argv", ["rating", "--uscf", "--verbose"])

    rating.main()

    output = capsys.readouterr().out
    assert "provider=uscf" in output
    assert "player_id=uscf-default" in output
    assert "standard=1500" in output
    assert "as_of=2026-03-30" in output
    assert "source_url=https://example.com/profile" in output


def test_main_selects_lichess_and_renders_json(monkeypatch, capsys):
    created = {}
    profile = _make_profile(provider="lichess", player_id="named-player", display_name="named-player")
    _FakeLoader.reset()

    class FakeLichess:
        def __init__(self, player, http_client):
            created["player"] = player
            created["http_client"] = http_client

        def fetch(self):
            return profile

        def getPrimaryRatingKey(self):
            return "standard"

    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(rating, "RequestsHttpAdapter", _FakeHttpClient)
    monkeypatch.setattr(rating, "Lichess", FakeLichess)
    monkeypatch.setattr(rating, "USCF", object)
    monkeypatch.setattr(rating, "ChessCom", object)
    monkeypatch.setattr(rating, "FIDE", object)
    monkeypatch.setattr("sys.argv", ["rating", "--lichess", "--json", "named-player"])

    rating.main()

    output = json.loads(capsys.readouterr().out)
    assert created["player"] == "named-player"
    assert isinstance(created["http_client"], _FakeHttpClient)
    assert output["provider"] == "lichess"
    assert output["player"]["id"] == "named-player"


def test_main_defaults_to_rapid_rating_for_chesscom(monkeypatch, capsys):
    created = {}
    profile = _make_profile(
        provider="chesscom",
        player_id="chess-default",
        display_name="chess-default",
        ratings=build_ratings(standard=1300, rapid=1200, blitz=1100),
    )
    _FakeLoader.reset()

    class FakeChessCom:
        def __init__(self, player, http_client):
            created["player"] = player
            created["http_client"] = http_client

        def fetch(self):
            return profile

        def getPrimaryRatingKey(self):
            return "rapid"

    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(rating, "RequestsHttpAdapter", _FakeHttpClient)
    monkeypatch.setattr(rating, "ChessCom", FakeChessCom)
    monkeypatch.setattr(rating, "USCF", object)
    monkeypatch.setattr(rating, "Lichess", object)
    monkeypatch.setattr(rating, "FIDE", object)
    monkeypatch.setattr("sys.argv", ["rating", "--chess"])

    rating.main()

    output = capsys.readouterr().out.strip()
    assert created["player"] == "chess-default"
    assert output == "1200"


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        ("--standard", "1500"),
        ("--rapid", "1450"),
        ("--blitz", "1400"),
        ("--bullet", "1350"),
        ("--correspondence", "1300"),
    ],
)
def test_main_displays_selected_rating(monkeypatch, capsys, option, expected):
    profile = _make_profile(
        provider="lichess",
        ratings=build_ratings(
            standard=1500,
            rapid=1450,
            blitz=1400,
            bullet=1350,
            correspondence=1300,
        ),
    )
    _FakeLoader.reset()

    class FakeLichess:
        def __init__(self, player, http_client):
            pass

        def fetch(self):
            return profile

    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(rating, "RequestsHttpAdapter", _FakeHttpClient)
    monkeypatch.setattr(rating, "Lichess", FakeLichess)
    monkeypatch.setattr(rating, "USCF", object)
    monkeypatch.setattr(rating, "ChessCom", object)
    monkeypatch.setattr(rating, "FIDE", object)
    monkeypatch.setattr("sys.argv", ["rating", "--lichess", option])

    rating.main()

    assert capsys.readouterr().out.strip() == expected


def test_main_formats_an_unrated_selection(monkeypatch, capsys):
    profile = _make_profile(provider="chesscom", ratings=build_ratings(rapid=1200))
    _FakeLoader.reset()

    class FakeChessCom:
        def __init__(self, player, http_client):
            pass

        def fetch(self):
            return profile

    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(rating, "RequestsHttpAdapter", _FakeHttpClient)
    monkeypatch.setattr(rating, "ChessCom", FakeChessCom)
    monkeypatch.setattr(rating, "USCF", object)
    monkeypatch.setattr(rating, "Lichess", object)
    monkeypatch.setattr(rating, "FIDE", object)
    monkeypatch.setattr("sys.argv", ["rating", "--chess", "--bullet"])

    rating.main()

    assert capsys.readouterr().out.strip() == "Not rated"


def test_main_selects_fide_and_handles_missing_profile(monkeypatch, capsys):
    created = {}
    _FakeLoader.reset()

    class FakeFIDE:
        def __init__(self, player, http_client):
            created["player"] = player
            created["http_client"] = http_client

        def fetch(self):
            return None

    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(rating, "RequestsHttpAdapter", _FakeHttpClient)
    monkeypatch.setattr(rating, "FIDE", FakeFIDE)
    monkeypatch.setattr(rating, "USCF", object)
    monkeypatch.setattr(rating, "Lichess", object)
    monkeypatch.setattr(rating, "ChessCom", object)
    monkeypatch.setattr("sys.argv", ["rating", "--fide"])

    rating.main()

    output = capsys.readouterr().out.strip()
    assert created["player"] == "fide-default"
    assert output == 'No ratings found for "fide-default"'


def test_main_config_prints_filename_and_contents(monkeypatch, capsys, tmp_path):
    _FakeLoader.reset()
    config_file = tmp_path / ".env"
    config_file.write_text("USCF_DEFAULT_USER=sample-player\n", encoding="utf-8")
    _FakeLoader.filename = str(config_file)
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating", "config"])

    rating.main()

    assert capsys.readouterr().out == (
        f"{config_file}\nUSCF_DEFAULT_USER=sample-player\n"
    )


def _capture_write_graph(monkeypatch, fake_path="/fake/path.png"):
    """Replace rating._write_graph with a fake that records its call and
    returns ``fake_path``, so tests can assert on selection logic without
    paying for real plotting."""
    calls = []

    def fake_write_graph(rows, provider, player, category, output_path):
        calls.append(
            {
                "rows": rows,
                "provider": provider,
                "player": player,
                "category": category,
                "output_path": output_path,
            }
        )
        return fake_path

    monkeypatch.setattr(rating, "_write_graph", fake_write_graph)
    return calls


def test_main_history_plots_a_graph_by_default(monkeypatch, capsys, tmp_path):
    from rating.adapters.sqlite_profile_log import SQLiteProfileLogAdapter

    database = tmp_path / "ratings.db"
    adapter = SQLiteProfileLogAdapter(database)
    adapter.log(_make_profile(provider="lichess", player_id="pehanna"))
    adapter.log(
        _make_profile(
            provider="lichess",
            player_id="pehanna",
            ratings=build_ratings(standard=1550, blitz=1400),
        )
    )
    calls = _capture_write_graph(monkeypatch)
    _FakeLoader.reset()
    _FakeLoader.config_overrides = {"DBFILE": str(database)}
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating", "history", "pehanna", "--lichess"])

    rating.main()

    assert capsys.readouterr().out.strip() == "Wrote /fake/path.png"
    assert len(calls) == 1
    assert calls[0]["provider"] == "lichess"
    assert calls[0]["player"] == "pehanna"
    assert calls[0]["category"] == "standard"
    assert calls[0]["rows"] == [("2026-03-30", 1500), ("2026-03-30", 1550)]


def test_main_history_respects_rating_key_flag(monkeypatch, capsys, tmp_path):
    from rating.adapters.sqlite_profile_log import SQLiteProfileLogAdapter

    database = tmp_path / "ratings.db"
    SQLiteProfileLogAdapter(database).log(
        _make_profile(
            provider="lichess",
            player_id="pehanna",
            ratings=build_ratings(standard=1500, blitz=1400),
        )
    )
    calls = _capture_write_graph(monkeypatch)
    _FakeLoader.reset()
    _FakeLoader.config_overrides = {"DBFILE": str(database)}
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating", "history", "pehanna", "--lichess", "--blitz"])

    rating.main()

    assert calls[0]["category"] == "blitz"
    assert calls[0]["rows"] == [("2026-03-30", 1400)]


def test_main_history_uses_configured_default_player_when_omitted(monkeypatch, capsys, tmp_path):
    from rating.adapters.sqlite_profile_log import SQLiteProfileLogAdapter

    database = tmp_path / "ratings.db"
    SQLiteProfileLogAdapter(database).log(
        _make_profile(provider="lichess", player_id="lichess-default")
    )
    calls = _capture_write_graph(monkeypatch)
    _FakeLoader.reset()
    _FakeLoader.config_overrides = {"DBFILE": str(database)}
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating", "history", "--lichess"])

    rating.main()

    assert calls[0]["player"] == "lichess-default"


def test_main_history_json_output(monkeypatch, capsys, tmp_path):
    from rating.adapters.sqlite_profile_log import SQLiteProfileLogAdapter

    database = tmp_path / "ratings.db"
    SQLiteProfileLogAdapter(database).log(_make_profile(provider="lichess", player_id="pehanna"))
    _FakeLoader.reset()
    _FakeLoader.config_overrides = {"DBFILE": str(database)}
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating", "history", "pehanna", "--lichess", "--json"])

    rating.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload == [{"as_of": "2026-03-30", "value": 1500}]


def test_main_history_reports_when_nothing_is_logged(monkeypatch, capsys, tmp_path):
    _FakeLoader.reset()
    _FakeLoader.config_overrides = {"DBFILE": str(tmp_path / "missing.db")}
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating", "history", "nobody", "--uscf"])

    rating.main()

    output = capsys.readouterr().out.strip()
    assert output == 'No "standard" history found for uscf player "nobody"'


def _hover_callback(fig):
    """Retrieve the motion_notify_event callback most recently connected to fig."""
    registry = fig.canvas.callbacks.callbacks["motion_notify_event"]
    cid = list(registry)[-1]
    return registry[cid]()


def test_hover_tooltip_shows_date_and_rating_for_the_hovered_point(monkeypatch):
    from datetime import datetime
    from types import SimpleNamespace

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    dates = [datetime(2026, 3, 30), datetime(2026, 4, 1)]
    values = [1500, 1550]
    (line,) = ax.plot(dates, values)
    rating._add_hover_tooltip(ax, line, dates, values, "blitz")
    monkeypatch.setattr(line, "contains", lambda event: (True, {"ind": [1]}))

    _hover_callback(fig)(SimpleNamespace(inaxes=ax))

    annotation = ax.texts[-1]
    assert annotation.get_visible()
    assert annotation.get_text() == "2026-04-01\nblitz: 1550"
    plt.close(fig)


def test_hover_tooltip_shows_not_rated_for_a_missing_value(monkeypatch):
    from datetime import datetime
    from types import SimpleNamespace

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    dates = [datetime(2026, 3, 30)]
    values = [float("nan")]
    (line,) = ax.plot(dates, values)
    rating._add_hover_tooltip(ax, line, dates, values, "standard")
    monkeypatch.setattr(line, "contains", lambda event: (True, {"ind": [0]}))

    _hover_callback(fig)(SimpleNamespace(inaxes=ax))

    assert ax.texts[-1].get_text() == "2026-03-30\nstandard: Not rated"
    plt.close(fig)


def test_hover_tooltip_hides_when_pointer_leaves_a_point_or_the_axes(monkeypatch):
    from datetime import datetime
    from types import SimpleNamespace

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    dates = [datetime(2026, 3, 30)]
    values = [1500]
    (line,) = ax.plot(dates, values)
    rating._add_hover_tooltip(ax, line, dates, values, "standard")
    callback = _hover_callback(fig)

    monkeypatch.setattr(line, "contains", lambda event: (True, {"ind": [0]}))
    callback(SimpleNamespace(inaxes=ax))
    assert ax.texts[-1].get_visible()

    monkeypatch.setattr(line, "contains", lambda event: (False, {}))
    callback(SimpleNamespace(inaxes=ax))
    assert not ax.texts[-1].get_visible()

    callback(SimpleNamespace(inaxes=None))
    assert not ax.texts[-1].get_visible()
    plt.close(fig)


def test_parse_when_handles_date_and_timestamp_formats():
    from datetime import datetime

    assert rating._parse_when("2026-03-30") == datetime(2026, 3, 30)
    assert rating._parse_when("2026-03-30 12:34:56") == datetime(2026, 3, 30, 12, 34, 56)


def test_main_history_writes_png_to_tmpdir_by_default(monkeypatch, capsys, tmp_path):
    import tempfile

    from rating.adapters.sqlite_profile_log import SQLiteProfileLogAdapter

    database = tmp_path / "ratings.db"
    SQLiteProfileLogAdapter(database).log(
        _make_profile(provider="lichess", player_id="pehanna")
    )
    _FakeLoader.reset()
    _FakeLoader.config_overrides = {"DBFILE": str(database)}
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating", "history", "pehanna", "--lichess"])

    expected = Path(tempfile.gettempdir()) / "lichess_pehanna_standard.png"
    try:
        rating.main()

        assert capsys.readouterr().out.strip() == f"Wrote {expected}"
        assert expected.is_file()
    finally:
        expected.unlink(missing_ok=True)


def test_main_history_respects_output_option(monkeypatch, capsys, tmp_path):
    from rating.adapters.sqlite_profile_log import SQLiteProfileLogAdapter

    database = tmp_path / "ratings.db"
    SQLiteProfileLogAdapter(database).log(
        _make_profile(provider="lichess", player_id="pehanna")
    )
    _FakeLoader.reset()
    _FakeLoader.config_overrides = {"DBFILE": str(database)}
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    output_path = tmp_path / "custom.png"
    monkeypatch.setattr(
        "sys.argv",
        ["rating", "history", "pehanna", "--lichess", "-o", str(output_path)],
    )

    rating.main()

    assert capsys.readouterr().out.strip() == f"Wrote {output_path}"
    assert output_path.is_file()


def test_main_help_exits_cleanly(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["rating", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        rating.main()

    assert exc_info.value.code == 0
    help_output = capsys.readouterr().out
    assert "Fetches and prints a players's chess rating" in help_output
    assert "rating config" in help_output
    assert "--standard" in help_output
    assert "--rapid" in help_output
    assert "--blitz" in help_output
    assert "--bullet" in help_output
    assert "--correspondence" in help_output
    assert "default except for Chess.com" in help_output
    assert "default for Chess.com" in help_output
