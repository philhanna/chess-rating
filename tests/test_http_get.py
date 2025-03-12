import pytest
import requests
from unittest.mock import patch, Mock

from rating import http_get

def test_http_get_success():
    """Test http_get with a successful response."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.text = "Mock response body"

    with patch("requests.get", return_value=mock_response):
        url = "https://example.com"
        result = http_get(url)

    assert result == "Mock response body"

def test_http_get_http_error():
    """Test http_get when the request returns an HTTP error."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

    with patch("requests.get", return_value=mock_response):
        url = "https://example.com"
        result = http_get(url)

    assert result is None

def test_http_get_network_error():
    """Test http_get when a network error occurs."""
    with patch("requests.get", side_effect=requests.ConnectionError("Network error")):
        url = "https://example.com"
        result = http_get(url)

    assert result is None

def test_http_get_timeout():
    """Test http_get when a timeout occurs."""
    with patch("requests.get", side_effect=requests.Timeout("Request timed out")):
        url = "https://example.com"
        result = http_get(url)

    assert result is None
