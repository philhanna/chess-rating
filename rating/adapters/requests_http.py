import sys
import requests

from rating.ports.http_port import HttpPort


class RequestsHttpAdapter(HttpPort):
    """Driven adapter: fulfils HttpPort using the requests library."""

    def get(self, url: str) -> str:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error: {e}", file=sys.stderr)
            return None
