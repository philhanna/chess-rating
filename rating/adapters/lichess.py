"""Lichess rating adapter.

This module translates the Lichess user API response into the compact
pipe-delimited format used by the rest of the application.
"""

import json

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class Lichess(RatingPort):
    """Fetch and normalize Lichess ratings for a single player."""

    def __init__(self, player: str, http_client: HttpPort = None):
        """Store the player identifier and injected HTTP client."""
        self.player = player
        self._http_client = http_client

    def fetch(self) -> str:
        """Request the player's profile and return normalized rating data."""
        url = self.get_url()
        content = self._http_client.get(url)
        if content is None:
            return None
        return self.parse_content(content)

    def get_url(self) -> str:
        """Build the Lichess API URL for the configured player."""
        return f"https://lichess.org/api/user/{self.player}"

    def parse_content(self, content: str) -> str:
        """Extract active performance ratings from the Lichess JSON payload."""
        jsonobj = json.loads(content)

        # Lichess returns many performance buckets; keep only categories that
        # actually have games played and a rating value.
        filtered_perfs = {
            category: value["rating"]
            for category, value in jsonobj["perfs"].items()
            if isinstance(value, dict) and "games" in value and value["games"] > 0 and "rating" in value
        }

        # Sort keys so repeated fetches produce stable output ordering.
        parts = [f"{category}={rating}" for category, rating in filtered_perfs.items()]
        parts.sort()
        parts.insert(0, f"username={self.player}")

        return "|".join(parts)
