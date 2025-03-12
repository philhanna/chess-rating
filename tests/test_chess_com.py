import json
import pytest
from rating.chesscom import ChessCom

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
    expected = "username=someplayer,blitz=2500,bullet=2600,rapid=2400"
    assert result == expected


def test_parse_content_missing_ratings():
    json_content = json.dumps({
        "chess_blitz": {},
        "chess_bullet": {},
        "chess_rapid": {}
    })
    chess_com_parser = ChessCom("someplayer")
    result = chess_com_parser.parse_content(json_content)
    expected = "username=someplayer"
    assert result == expected


def test_parse_content_no_chess_categories():
    json_content = json.dumps({
        "other_category": {"last": {"rating": 2000}}
    })
    chess_com_parser = ChessCom("someplayer")
    result = chess_com_parser.parse_content(json_content)
    expected = "username=someplayer"
    assert result == expected


def test_parse_content_empty_json():
    json_content = json.dumps({})
    chess_com_parser = ChessCom("someplayer")
    result = chess_com_parser.parse_content(json_content)
    expected = "username=someplayer"
    assert result == expected


def test_parse_content_invalid_json():
    json_content = "{invalid_json: true,}"  # Malformed JSON
    chess_com_parser = ChessCom("someplayer")
    with pytest.raises(json.JSONDecodeError):
        chess_com_parser.parse_content(json_content)
