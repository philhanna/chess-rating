from bs4 import BeautifulSoup

from rating.uscf import USCF

def test_extract_player_count_valid():
    html_content = """
    <td colspan='7'>Players found: 3</td>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    result = USCF.extract_player_count(soup)
    assert result == 3


def test_extract_player_count_zero():
    html_content = """
    <td colspan='7'>Players found: 0</td>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    result = USCF.extract_player_count(soup)
    assert result == 0


def test_extract_player_count_missing():
    html_content = """
    <td colspan='7'>No players found</td>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    result = USCF.extract_player_count(soup)
    assert result == 0


def test_extract_player_count_malformed():
    html_content = """
    <td colspan='7'>Players found: ABC</td>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    result = USCF.extract_player_count(soup)
    assert result == 0


def test_extract_player_count_no_colspan():
    html_content = """
    <td>Players found: 5</td>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    result = USCF.extract_player_count(soup)
    assert result == 0


def test_extract_headers_valid():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 2</td></tr>
        <tr><td>ID</td><td>Name</td><td>Rating</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    uscf_parser = USCF("someplayer")
    result = uscf_parser.extract_headers(soup)
    assert result == ["ID", "Name", "Rating"]


def test_extract_headers_missing():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 2</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    uscf_parser = USCF("someplayer")
    result = uscf_parser.extract_headers(soup)
    assert result == []


def test_extract_headers_extra_whitespace():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 2</td></tr>
        <tr><td> ID </td><td> Name  </td><td> Rating </td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    uscf_parser = USCF("someplayer")
    result = uscf_parser.extract_headers(soup)
    assert result == ["ID", "Name", "Rating"]


def test_extract_headers_with_special_characters():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><td>Player ID</td><td>Player Name</td><td>Rating (USCF)</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    uscf_parser = USCF("someplayer")
    result = uscf_parser.extract_headers(soup)
    assert result == ["Player_ID", "Player_Name", "Rating_(USCF)"]


def test_extract_headers_unexpected_structure():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><th>ID</th><th>Name</th><th>Rating</th></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    uscf_parser = USCF("someplayer")
    result = uscf_parser.extract_headers(soup)
    assert result == []


def test_extract_player_data_valid():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><td>ID</td><td>Name</td><td>Rating</td></tr>
        <tr><td>12345</td><td>John Doe</td><td>2000</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    uscf_parser = USCF("someplayer")
    headers = ["ID", "Name", "Rating"]
    result = uscf_parser.extract_player_data(soup, headers, 1)
    expected = "ID=12345,Name=John Doe,Rating=2000"
    assert result == expected


def test_parse_content_no_players():
    html_content = """
    <td colspan='7'>Players found: 0</td>
    """
    uscf_parser = USCF("someplayer")
    result = uscf_parser.parse_content(html_content)
    assert result == ""