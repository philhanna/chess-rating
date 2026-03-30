"""Requests-based implementation of the outbound HTTP port."""

import sys
import requests

from rating.ports.http_port import HttpPort


class RequestsHttpAdapter(HttpPort):
    """Fulfil :class:`HttpPort` with the third-party ``requests`` client."""

    def get(self, url: str) -> str:
        """Return the response body for ``url`` or ``None`` if the request fails."""
        try:
            # Some provider endpoints are more reliable when the request looks
            # like it came from a regular browser session.
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            # Keep infrastructure failures visible without crashing the caller.
            print(f"Error: {e}", file=sys.stderr)
            return None
