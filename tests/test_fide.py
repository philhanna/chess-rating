import pytest
from unittest.mock import Mock

from rating.adapters.fide import FIDE
from rating.ports.http_port import HttpPort


def test_fide_initialization():
    player_name = "Magnus Carlsen"
    fide = FIDE(player_name)
    assert fide.player == player_name


def test_fide_get_url():
    player_name = "12345678"  # Assuming FIDE ID instead of name
    fide = FIDE(player_name)
    expected_url = f"https://ratings.fide.com/profile/{player_name}"
    assert fide.get_url() == expected_url


def test_parse_content_valid():
    html_content = """
    <div class="profile-container">
        <h1 class="player-title">Magnus Carlsen</h1>
    </div>
    <div class="profile-section">
        <div class="profile-games">
            <div>
                <p>2835</p>
                <p>Standard</p>
            </div>
            <div>
                <p>2810</p>
                <p>Rapid</p>
            </div>
            <div>
                <p>2885</p>
                <p>Blitz</p>
            </div>
        </div>
    </div>
    """
    fide_parser = FIDE("someplayer")
    result = fide_parser.parse_content(html_content)
    assert result.provider == "fide"
    assert result.player.id == "someplayer"
    assert result.player.display_name == "Magnus Carlsen"
    assert result.ratings["standard"] == 2835
    assert result.ratings["rapid"] == 2810
    assert result.ratings["blitz"] == 2885


def test_parse_content_missing_profile_container():
    html_content = """
    <div class="profile-section">
        <div class="profile-games">
            <div>
                <p>2835</p>
                <p>Standard</p>
            </div>
        </div>
    </div>
    """
    fide_parser = FIDE("someplayer")
    result = fide_parser.parse_content(html_content)
    assert result is None


def test_parse_content_missing_player_title():
    html_content = """
    <div class="profile-container">
    </div>
    <div class="profile-section">
        <div class="profile-games">
            <div>
                <p>2835</p>
                <p>Standard</p>
            </div>
        </div>
    </div>
    """
    fide_parser = FIDE("someplayer")
    result = fide_parser.parse_content(html_content)
    assert result is None


def test_parse_content_missing_profile_section():
    html_content = """
    <div class="profile-container">
        <h1 class="player-title">Magnus Carlsen</h1>
    </div>
    """
    fide_parser = FIDE("someplayer")
    with pytest.raises(AssertionError):    
        fide_parser.parse_content(html_content)


def test_parse_content_missing_profile_games():
    html_content = """
    <div class="profile-container">
        <h1 class="player-title">Magnus Carlsen</h1>
    </div>
    <div class="profile-section">
    </div>
    """
    fide_parser = FIDE("someplayer")
    result = fide_parser.parse_content(html_content)
    assert result.player.display_name == "Magnus Carlsen"
    assert all(value is None for value in result.ratings.values())
    assert result.extras == {}


def test_parse_content_malformed_games():
    html_content = """
    <div class="profile-container">
        <h1 class="player-title">Magnus Carlsen</h1>
    </div>
    <div class="profile-section">
        <div class="profile-games">
            <div>
                <p>2835</p>
            </div>
        </div>
    </div>
    """
    fide_parser = FIDE("someplayer")
    with pytest.raises(AssertionError):
        fide_parser.parse_content(html_content)


def test_fetch_returns_normalized_profile_from_http_response():
    html_content = """
    <div class="profile-container">
        <h1 class="player-title">Magnus Carlsen</h1>
    </div>
    <div class="profile-section">
        <div class="profile-games">
            <div>
                <p>2835</p>
                <p>Standard</p>
            </div>
            <div>
                <p>2810</p>
                <p>Rapid</p>
            </div>
            <div>
                <p>Not rated</p>
                <p>Blitz</p>
            </div>
            <div>
                <p>2400</p>
                <p>Bullet Arena</p>
            </div>
        </div>
    </div>
    """
    http_client = Mock(spec=HttpPort)
    http_client.get.return_value = html_content

    fide = FIDE("1503014", http_client)

    result = fide.fetch()

    assert result.provider == "fide"
    assert result.player.id == "1503014"
    assert result.player.display_name == "Magnus Carlsen"
    assert result.ratings["standard"] == 2835
    assert result.ratings["rapid"] == 2810
    assert result.ratings["blitz"] is None
    assert result.extras["bullet_arena"] == 2400
    assert result.metadata.source_url == "https://ratings.fide.com/profile/1503014"
    http_client.get.assert_called_once_with("https://ratings.fide.com/profile/1503014")


def test_fetch_returns_none_when_http_client_returns_none():
    http_client = Mock(spec=HttpPort)
    http_client.get.return_value = None

    fide = FIDE("1503014", http_client)

    result = fide.fetch()

    assert result is None
    http_client.get.assert_called_once_with("https://ratings.fide.com/profile/1503014")
