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

