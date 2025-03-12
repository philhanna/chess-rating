import pytest
from rating.fide import FIDE


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
    expected = 'Username="Magnus Carlsen",Standard=2835,Rapid=2810,Blitz=2885'
    assert result == expected


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
    assert result == 'Username="Magnus Carlsen"'


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
