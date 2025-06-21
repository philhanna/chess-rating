from bs4 import BeautifulSoup

from rating.uscf import USCF

def test_extract_player_data_valid():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 2</td></tr>
        <tr><td>ID</td><td>Name</td><td>Rating</td></tr>
        <tr><td>12345</td><td>John Doe</td><td>2000</td></tr>
        <tr><td>67890</td><td>Jane Smith</td><td>1800</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = ["ID", "Name", "Rating"]
    result = USCF.extract_player_data(soup, headers, 2)
    expected = "ID=12345|Name=John Doe|Rating=2000\nID=67890|Name=Jane Smith|Rating=1800"
    assert result == expected


def test_extract_player_data_unrated():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><td>ID</td><td>Name</td><td>Rating</td></tr>
        <tr><td>54321</td><td>Alice Brown</td><td>Unrated</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = ["ID", "Name", "Rating"]
    result = USCF.extract_player_data(soup, headers, 1)
    expected = "ID=54321|Name=Alice Brown"
    assert result == expected


def test_extract_player_data_missing_columns():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><td>ID</td><td>Name</td></tr>
        <tr><td>99999</td><td>Bob White</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = ["ID", "Name", "Rating"]
    result = USCF.extract_player_data(soup, headers, 1)
    assert result == ""


def test_extract_player_data_more_players_than_exist():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 1</td></tr>
        <tr><td>ID</td><td>Name</td><td>Rating</td></tr>
        <tr><td>88888</td><td>Charlie Green</td><td>1900</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = ["ID", "Name", "Rating"]
    result = USCF.extract_player_data(soup, headers, 2)
    expected = "ID=88888|Name=Charlie Green|Rating=1900"
    assert result == expected


def test_extract_player_data_no_players():
    html_content = """
    <table>
        <tr><td colspan='7'>Players found: 0</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = ["ID", "Name", "Rating"]
    result = USCF.extract_player_data(soup, headers, 0)
    assert result == ""
