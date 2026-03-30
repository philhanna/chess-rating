import pytest
import json
from unittest.mock import Mock

from rating.adapters.lichess import Lichess
from rating.ports.http_port import HttpPort

@pytest.fixture
def sample_json():
    return json.dumps({
        "id": "testplayer",
        "username": "testplayer",
        "perfs": {
            "bullet": {"games": 5, "rating": 1500},
            "blitz": {"games": 10, "rating": 1600},
            "rapid": {"games": 0, "rating": 1400},  # Should be ignored
            "classical": {"games": 7, "rating": 1700}
        }
    })

@pytest.fixture
def empty_json():
    return json.dumps({
        "id": "testplayer",
        "username": "testplayer",
        "perfs": {}
    })

@pytest.fixture
def lichess_instance():
    return Lichess("testplayer")


def test_get_url(lichess_instance):
    expected_url = "https://lichess.org/api/user/testplayer"
    assert lichess_instance.get_url() == expected_url


def test_parse_content(lichess_instance, sample_json, empty_json):
    result = lichess_instance.parse_content(sample_json)
    assert result.provider == "lichess"
    assert result.player.id == "testplayer"
    assert result.player.display_name == "testplayer"
    assert result.ratings["standard"] == 1700
    assert result.ratings["blitz"] == 1600
    assert result.ratings["bullet"] == 1500
    assert result.ratings["rapid"] is None

    empty_result = lichess_instance.parse_content(empty_json)
    assert all(value is None for value in empty_result.ratings.values())
    assert empty_result.extras == {}


def test_parse_content_maps_provider_specific_categories_to_extras():
    json_content = json.dumps({
        "id": "testplayer",
        "username": "Test Player",
        "perfs": {
            "puzzle": {"games": 3, "rating": 2100},
            "ultraBullet": {"games": 8, "rating": 1800},
            "correspondence": {"games": 4, "rating": 1550},
        }
    })
    lichess = Lichess("fallback-player")

    result = lichess.parse_content(json_content)

    assert result.player.id == "testplayer"
    assert result.player.display_name == "Test Player"
    assert result.ratings["correspondence"] == 1550
    assert result.extras["puzzle"] == 2100
    assert result.extras["ultra_bullet"] == 1800


def test_fetch_returns_normalized_profile_from_http_response(sample_json):
    http_client = Mock(spec=HttpPort)
    http_client.get.return_value = sample_json

    lichess = Lichess("testplayer", http_client)

    result = lichess.fetch()

    assert result.provider == "lichess"
    assert result.ratings["standard"] == 1700
    assert result.ratings["blitz"] == 1600
    assert result.ratings["bullet"] == 1500
    assert result.metadata.source_url == "https://lichess.org/api/user/testplayer"
    http_client.get.assert_called_once_with("https://lichess.org/api/user/testplayer")


def test_fetch_returns_none_when_http_client_returns_none():
    http_client = Mock(spec=HttpPort)
    http_client.get.return_value = None

    lichess = Lichess("testplayer", http_client)

    result = lichess.fetch()

    assert result is None
    http_client.get.assert_called_once_with("https://lichess.org/api/user/testplayer")
