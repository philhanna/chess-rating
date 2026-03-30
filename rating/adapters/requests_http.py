"""Requests-based implementation of the outbound HTTP port."""

import sys
import requests

from rating.ports.http_port import HttpPort


class RequestsHttpAdapter(HttpPort):
    """Fulfil :class:`HttpPort` with the third-party ``requests`` client.

    This adapter is the infrastructure boundary between the application and
    the ``requests`` library. It keeps transport concerns out of the rating
    adapters so they can focus strictly on provider-specific parsing.
    """

    def get(self, url: str) -> str:
        """Return the response body for ``url`` or ``None`` if the request fails.

        Parameters
        ----------
        url:
            Fully qualified URL to request with HTTP GET.
        """
        try:
            # Some provider endpoints are more reliable when the request looks
            # like it came from a regular browser session.
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            }
            # Allow requests to raise a provider-specific error for non-2xx
            # responses so callers can handle all failures uniformly.
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            # Keep infrastructure failures visible without crashing the caller.
            print(f"Error: {e}", file=sys.stderr)
            return None
