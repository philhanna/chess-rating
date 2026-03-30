import json
import pytest
from unittest.mock import Mock

from rating.adapters.chesscom import ChessCom
from rating.ports.http_port import HttpPort

def test_chesscom_initialization():
    """Test that ChessCom initializes with the correct player name."""
    player = "pehanna7"
    chess_player = ChessCom(player)
    assert chess_player.player == player, "Player name should be correctly stored."

def test_chesscom_get_url():
    """Test that ChessCom generates the correct Chess.com API URL."""
    player = "pehanna7"
    chess_player = ChessCom(player)
    expected_url = f"https://api.chess.com/pub/player/{player}/stats"
    assert chess_player.get_url() == expected_url, "URL should be correctly formatted."

def test_chesscom_get_url_special_characters():
    """Test ChessCom with a player name containing special characters."""
    player = "magnus-carlsen"
    chess_player = ChessCom(player)
    expected_url = f"https://api.chess.com/pub/player/{player}/stats"
    assert chess_player.get_url() == expected_url, "URL should handle hyphens correctly."

def test_chesscom_get_url_case_insensitivity():
    """Test ChessCom URL generation for a case-insensitive username."""
    player = "MAGNUSCARLSEN"
    chess_player = ChessCom(player)
    expected_url = "https://api.chess.com/pub/player/magnuscarlsen/stats"
    assert chess_player.get_url().lower() == expected_url.lower(), "URL should handle case insensitivity."


def test_parse_content_valid():
    json_content = json.dumps({
        "chess_blitz": {"last": {"rating": 2500}},
        "chess_bullet": {"last": {"rating": 2600}},
        "chess_rapid": {"last": {"rating": 2400}}
    })
    chess_com_parser = ChessCom("someplayer")
    result = chess_com_parser.parse_content(json_content)
    assert result.provider == "chesscom"
    assert result.player.id == "someplayer"
    assert result.player.display_name == "someplayer"
    assert result.ratings["blitz"] == 2500
    assert result.ratings["bullet"] == 2600
    assert result.ratings["rapid"] == 2400
    assert result.ratings["standard"] is None
    assert result.metadata.source_url == "https://api.chess.com/pub/player/someplayer/stats"


def test_parse_content_missing_ratings():
    json_content = json.dumps({
        "chess_blitz": {},
        "chess_bullet": {},
        "chess_rapid": {}
    })
    chess_com_parser = ChessCom("someplayer")
    result = chess_com_parser.parse_content(json_content)
    assert all(value is None for value in result.ratings.values())
    assert result.extras == {}


def test_parse_content_no_chess_categories():
    json_content = json.dumps({
        "other_category": {"last": {"rating": 2000}}
    })
    chess_com_parser = ChessCom("someplayer")
    result = chess_com_parser.parse_content(json_content)
    assert all(value is None for value in result.ratings.values())
    assert result.extras == {}


def test_parse_content_empty_json():
    json_content = json.dumps({})
    chess_com_parser = ChessCom("someplayer")
    result = chess_com_parser.parse_content(json_content)
    assert result.player.id == "someplayer"
    assert all(value is None for value in result.ratings.values())
    assert result.extras == {}


def test_parse_content_invalid_json():
    json_content = "{invalid_json: true,}"  # Malformed JSON
    chess_com_parser = ChessCom("someplayer")
    with pytest.raises(json.JSONDecodeError):
        chess_com_parser.parse_content(json_content)


def test_fetch_returns_normalized_output_from_http_response():
    json_content = json.dumps({
        "chess_blitz": {"last": {"rating": 2500}},
        "chess_bullet": {"last": {"rating": 2600}},
    })
    http_client = Mock(spec=HttpPort)
    http_client.get.return_value = json_content

    chess_player = ChessCom("someplayer", http_client)

    result = chess_player.fetch()

    assert result.ratings["blitz"] == 2500
    assert result.ratings["bullet"] == 2600
    assert result.provider == "chesscom"
    http_client.get.assert_called_once_with("https://api.chess.com/pub/player/someplayer/stats")


def test_fetch_returns_none_when_http_client_returns_none():
    http_client = Mock(spec=HttpPort)
    http_client.get.return_value = None

    chess_player = ChessCom("someplayer", http_client)

    result = chess_player.fetch()

    assert result is None
    http_client.get.assert_called_once_with("https://api.chess.com/pub/player/someplayer/stats")
