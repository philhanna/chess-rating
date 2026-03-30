import pytest
import json

from rating.adapters.lichess import Lichess

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
