"""Chess.com rating adapter.

This module reads the Chess.com public stats endpoint and converts the
available chess_* ratings into the application's normalized string format.
"""

import json

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class ChessCom(RatingPort):
    """Fetch and normalize Chess.com ratings for a single player."""

    def __init__(self, player: str, http_client: HttpPort = None):
        """Store the player identifier and injected HTTP client."""
        self.player = player
        self._http_client = http_client

    def fetch(self) -> str:
        """Request the player's stats document and parse it into output text."""
        url = self.get_url()
        content = self._http_client.get(url)
        if content is None:
            return None
        return self.parse_content(content)

    def get_url(self) -> str:
        """Build the Chess.com stats endpoint for the configured player."""
        return f"https://api.chess.com/pub/player/{self.player}/stats"

    def parse_content(self, content: str) -> str:
        """Extract published Chess.com ratings from the JSON response."""
        parsed_data = json.loads(content)

        # The API exposes multiple sections; only keep rating-bearing chess_*
        # entries and read the latest published rating from each one.
        ratings = {
            key: value["last"].get("rating", "N/A")
            for key, value in parsed_data.items()
            if key.startswith("chess_") and isinstance(value, dict) and "last" in value
        }

        # Strip the common chess_ prefix so the output keys stay concise.
        parts = [f"{key.split('_', 1)[1]}={rating}" for key, rating in ratings.items()]
        parts.sort()
        parts.insert(0, f"username={self.player}")

        return "|".join(parts)
