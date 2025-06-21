from rating.uscf import USCF


def test_get_url():
    uscf_parser = USCF("John Doe")
    expected_url = "https://www.uschess.org/datapage/player-search.php?name=John+Doe&state=ANY"
    assert uscf_parser.get_url() == expected_url


def test_get_url_special_characters():
    uscf_parser = USCF("John O'Neil")
    expected_url = "https://www.uschess.org/datapage/player-search.php?name=John+O%27Neil&state=ANY"
    assert uscf_parser.get_url() == expected_url


def test_parse_content_valid():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><td>ID</td><td>Name</td><td>Rating</td></tr>
        <tr><td>12345</td><td>John Doe</td><td>2000</td></tr>
    </table>
    """
    uscf_parser = USCF("someplayer")
    result = uscf_parser.parse_content(html_content)
    expected = "ID=12345|Name=John Doe|Rating=2000"
    assert result == expected


def test_parse_content_no_players():
    html_content = """
    <td colspan='7'>Players found: 0</td>
    """
    uscf_parser = USCF("someplayer")
    result = uscf_parser.parse_content(html_content)
    assert result == ""


def test_parse_content_missing_headers():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><td>12345</td><td>John Doe</td><td>2000</td></tr>
    </table>
    """
    uscf_parser = USCF("someplayer")
    result = uscf_parser.parse_content(html_content)
    assert result == ""


def test_parse_content_unrated_player():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><td>ID</td><td>Name</td><td>Rating</td></tr>
        <tr><td>67890</td><td>Jane Doe</td><td>Unrated</td></tr>
    </table>
    """
    uscf_parser = USCF("someplayer")
    result = uscf_parser.parse_content(html_content)
    expected = "ID=67890|Name=Jane Doe"
    assert result == expected
