import json

import pytest

from rating.application import rating
from rating.domain.models import (
    NormalizedRatingProfile,
    PlayerIdentity,
    RatingMetadata,
    build_ratings,
)


def _make_profile(provider="uscf", player_id="player1", display_name="Player One"):
    return NormalizedRatingProfile(
        provider=provider,
        player=PlayerIdentity(id=player_id, display_name=display_name),
        ratings=build_ratings(standard=1500, blitz=1400),
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


class _FakeLoader:
    filename = "/tmp/test-config.yaml"

    def __init__(self, *_args, **_kwargs):
        self.filename = self.__class__.filename
        self.config = {
            "USCF": {"defaultUser": "uscf-default"},
            "lichess": {"defaultUser": "lichess-default"},
            "Chess": {"defaultUser": "chess-default"},
            "FIDE": {"defaultUser": "fide-default"},
        }

    @classmethod
    def reset(cls):
        cls.filename = "/tmp/test-config.yaml"


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


def test_main_selects_uscf_and_uses_plain_output(monkeypatch, capsys):
    created = {}
    profile = _make_profile(provider="uscf", player_id="uscf-default", display_name="uscf-default")
    _FakeLoader.reset()

    class FakeUSCF:
        def __init__(self, player, http_client):
            created["player"] = player
            created["http_client"] = http_client

        def fetch(self):
            return profile

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
    assert "provider=uscf" in output
    assert "player_id=uscf-default" in output


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


def test_main_selects_chesscom_with_default_player(monkeypatch, capsys):
    created = {}
    profile = _make_profile(provider="chesscom", player_id="chess-default", display_name="chess-default")
    _FakeLoader.reset()

    class FakeChessCom:
        def __init__(self, player, http_client):
            created["player"] = player
            created["http_client"] = http_client

        def fetch(self):
            return profile

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
    assert "provider=chesscom" in output


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
    config_file = tmp_path / "config.yaml"
    config_file.write_text("USCF:\n  defaultUser: sample-player\n", encoding="utf-8")
    _FakeLoader.filename = str(config_file)
    monkeypatch.setattr(rating, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr("sys.argv", ["rating", "config"])

    rating.main()

    assert capsys.readouterr().out == (
        f"{config_file}\nUSCF:\n  defaultUser: sample-player\n"
    )


def test_main_help_exits_cleanly(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["rating", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        rating.main()

    assert exc_info.value.code == 0
    help_output = capsys.readouterr().out
    assert "Fetches and prints a players's chess rating" in help_output
    assert "rating config" in help_output
