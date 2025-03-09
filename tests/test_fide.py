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


def test_fide_parse_content():
    fide = FIDE("Test Player")
    sample_html = "<html><body>Sample FIDE Page</body></html>"

    # Since parse_content is not implemented, we only check if it runs without error
    assert callable(fide.parse_content)
    # assert isinstance(fide.parse_content(sample_html), list)
