from unittest.mock import Mock

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort
from rating.adapters.uscf import USCF


def test_fetch_chains_http_and_parse():
    """fetch() should call http_client.get() with the adapter's URL and parse the result."""
    mock_http = Mock(spec=HttpPort)
    mock_http.get.return_value = None

    uscf = USCF("testplayer", mock_http)
    result = uscf.fetch()

    mock_http.get.assert_called_once_with(uscf.get_url())
    assert result is None


def test_rating_port_is_abstract():
    """RatingPort cannot be instantiated directly."""
    try:
        RatingPort()
        assert False, "Should have raised TypeError"
    except TypeError:
        pass


def test_http_port_is_abstract():
    """HttpPort cannot be instantiated directly."""
    try:
        HttpPort()
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
