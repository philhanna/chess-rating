import pytest
import requests
from unittest.mock import patch, Mock

from rating.adapters.requests_http import RequestsHttpAdapter


@pytest.fixture
def adapter():
    return RequestsHttpAdapter()


def test_http_get_success(adapter):
    """Test get() with a successful response."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.text = "Mock response body"

    with patch("requests.get", return_value=mock_response):
        result = adapter.get("https://example.com")

    assert result == "Mock response body"


def test_http_get_http_error(adapter):
    """Test get() when the request returns an HTTP error."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

    with patch("requests.get", return_value=mock_response):
        result = adapter.get("https://example.com")

    assert result is None


def test_http_get_network_error(adapter):
    """Test get() when a network error occurs."""
    with patch("requests.get", side_effect=requests.ConnectionError("Network error")):
        result = adapter.get("https://example.com")

    assert result is None


def test_http_get_timeout(adapter):
    """Test get() when a timeout occurs."""
    with patch("requests.get", side_effect=requests.Timeout("Request timed out")):
        result = adapter.get("https://example.com")

    assert result is None
