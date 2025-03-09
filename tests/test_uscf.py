import pytest
from bs4 import BeautifulSoup

from rating.uscf import USCF


@pytest.fixture
def sample_html():
    return """
    <html>
        <body>
            <table>
                <tr>
                    <td colspan="7">Players found: 2</td>
                </tr>
                <tr>
                    <td>Name</td>
                    <td>ID</td>
                    <td>Rating</td>
                </tr>
                <tr>
                    <td>John Doe</td>
                    <td>12345</td>
                    <td>2000</td>
                </tr>
                <tr>
                    <td>Jane Smith</td>
                    <td>67890</td>
                    <td>1800</td>
                </tr>
            </table>
        </body>
    </html>
    """

@pytest.fixture
def empty_html():
    return """
    <html>
        <body>
            <table>
                <tr>
                    <td colspan="7">Players found: 0</td>
                </tr>
            </table>
        </body>
    </html>
    """

@pytest.fixture
def uscf_instance():
    return USCF("John Doe")


def test_extract_player_count(uscf_instance, sample_html, empty_html):
    soup = BeautifulSoup(sample_html, 'html.parser')
    assert uscf_instance.extract_player_count(soup) == 2
    
    soup = BeautifulSoup(empty_html, 'html.parser')
    assert uscf_instance.extract_player_count(soup) == 0


def test_extract_headers(uscf_instance, sample_html):
    soup = BeautifulSoup(sample_html, 'html.parser')
    expected_headers = ["Name", "ID", "Rating"]
    assert uscf_instance.extract_headers(soup) == expected_headers


def test_extract_player_data(uscf_instance, sample_html):
    soup = BeautifulSoup(sample_html, 'html.parser')
    headers = ["Name", "ID", "Rating"]
    expected_data = ["Name=John Doe,ID=12345,Rating=2000", "Name=Jane Smith,ID=67890,Rating=1800"]
    
    assert uscf_instance.extract_player_data(soup, headers, 2) == expected_data


def test_parse_content(uscf_instance, sample_html, empty_html):
    assert uscf_instance.parse_content(sample_html) == ["Name=John Doe,ID=12345,Rating=2000", "Name=Jane Smith,ID=67890,Rating=1800"]
    assert uscf_instance.parse_content(empty_html) == []
