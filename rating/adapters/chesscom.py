"""Chess.com rating adapter.

This module reads the Chess.com public stats endpoint and converts the
available chess_* ratings into the application's normalized string format.
"""

import json

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class ChessCom(RatingPort):
    """Fetch and normalize Chess.com ratings for a single player.

    The adapter is responsible for three things:
    1. Building the correct public Chess.com stats URL for the player.
    2. Delegating the network request to the injected :class:`HttpPort`.
    3. Converting the provider-specific JSON document into the compact
       pipe-delimited string used by the rest of this application.

    Parameters
    ----------
    player:
        Chess.com username to query.
    http_client:
        Concrete HTTP adapter used to perform outbound requests.
    """

    def __init__(self, player: str, http_client: HttpPort = None):
        """Initialize the adapter with a username and HTTP dependency."""
        self.player = player
        self._http_client = http_client

    def fetch(self) -> str:
        """Fetch and normalize the configured player's Chess.com ratings.

        Returns
        -------
        str | None
            Pipe-delimited rating output on success, or ``None`` if the
            underlying HTTP request fails.
        """
        url = self.get_url()
        content = self._http_client.get(url)
        if content is None:
            return None
        # Keep HTTP concerns separate from parsing so the transformation logic
        # stays easy to test with canned payloads.
        return self.parse_content(content)

    def get_url(self) -> str:
        """Build the Chess.com stats endpoint for the configured player."""
        return f"https://api.chess.com/pub/player/{self.player}/stats"

    def parse_content(self, content: str) -> str:
        """Extract published Chess.com ratings from the JSON response.

        The Chess.com stats payload includes many sections. Only keys beginning
        with ``chess_`` represent rating categories we want to expose, such as
        rapid, blitz, or bullet.
        """
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
        # Sort the categories to produce deterministic output regardless of the
        # JSON field order returned by the remote API.
        parts.sort()
        parts.insert(0, f"username={self.player}")

        return "|".join(parts)
