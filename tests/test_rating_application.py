import json
import runpy

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

    assert "provider=uscf" in result
    assert "player_id=player1" in result
    assert "display_name=Player One" in result
    assert "standard=1500" in result
    assert "rapid=Not rated" in result
    assert "blitz=1400" in result
    assert "puzzle=2000" in result
    assert "as_of=2026-03-30" in result


class _FakeLoader:
    def __init__(self, *_args, **_kwargs):
        self.config = {
            "USCF": {"defaultUser": "uscf-default"},
            "lichess": {"defaultUser": "lichess-default"},
            "Chess": {"defaultUser": "chess-default"},
            "FIDE": {"defaultUser": "fide-default"},
        }


class _FakeHttpClient:
    pass


def test_main_defaults_to_uscf_and_uses_plain_output(monkeypatch, capsys):
    created = {}
    profile = _make_profile(provider="uscf", player_id="uscf-default", display_name="uscf-default")

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
    monkeypatch.setattr("sys.argv", ["rating"])

    rating.main()

    output = capsys.readouterr().out.strip()
    assert created["player"] == "uscf-default"
    assert isinstance(created["http_client"], _FakeHttpClient)
    assert "provider=uscf" in output
    assert "player_id=uscf-default" in output


def test_main_selects_lichess_and_renders_json(monkeypatch, capsys):
    created = {}
    profile = _make_profile(provider="lichess", player_id="named-player", display_name="named-player")

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


def test_module_main_guard_executes(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["rating", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("rating.application.rating", run_name="__main__")

    assert exc_info.value.code == 0
    assert "Fetches and prints a players's chess rating" in capsys.readouterr().out
