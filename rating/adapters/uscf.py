"""US Chess Federation rating adapter.

This module talks to the USCF ratings API and returns the most recent section
rating in the normalized pipe-delimited format expected by the application.
"""

import json
import urllib

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class USCF(RatingPort):
    """Fetch and normalize USCF rating data for a single player."""

    def __init__(self, player: str, http_client: HttpPort = None):
        """Store the player identifier and injected HTTP client."""
        self.player = str(player)
        self._http_client = http_client

    def fetch(self) -> str:
        """Request the player's section history and parse the newest rating."""
        url = self.get_url()
        content = self._http_client.get(url)
        if content is None:
            return None
        return self.parse_content(content)

    def get_url(self) -> str:
        """Build the USCF endpoint, escaping the player identifier for URLs."""
        player_encoded = urllib.parse.quote_plus(self.player)
        return f"https://ratings-api.uschess.org/api/v1/members/{player_encoded}/sections"

    def parse_content(self, json_string: str) -> str:
        """Extract the latest section end date and post-rating from the payload."""
        data = json.loads(json_string)
        # The API returns sections in newest-first order, so the first item
        # represents the latest published rating snapshot.
        date = data["items"][0]["endDate"]
        rating = data["items"][0]["ratingRecords"][0]["postRating"]
        return f"player={self.player}|date={date}|rating={rating}"
