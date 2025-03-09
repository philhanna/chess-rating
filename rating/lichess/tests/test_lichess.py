import pytest
import json

from rating.lichess.lichess import Lichess

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
    expected_result = ["username=testplayer,blitz=1600,bullet=1500,classical=1700"]
    assert lichess_instance.parse_content(sample_json) == expected_result
    
    assert lichess_instance.parse_content(empty_json) == ["username=testplayer"]
