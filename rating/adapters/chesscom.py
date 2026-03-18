import json

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class ChessCom(RatingPort):
    """Driven adapter: fetches Chess.com rating information."""

    def __init__(self, player: str, http_client: HttpPort = None):
        self.player = player
        self._http_client = http_client

    def fetch(self) -> str:
        url = self.get_url()
        content = self._http_client.get(url)
        if content is None:
            return None
        return self.parse_content(content)

    def get_url(self) -> str:
        return f"https://api.chess.com/pub/player/{self.player}/stats"

    def parse_content(self, content: str) -> str:
        parsed_data = json.loads(content)

        ratings = {
            key: value["last"].get("rating", "N/A")
            for key, value in parsed_data.items()
            if key.startswith("chess_") and isinstance(value, dict) and "last" in value
        }

        parts = [f"{key.split('_', 1)[1]}={rating}" for key, rating in ratings.items()]
        parts.sort()
        parts.insert(0, f"username={self.player}")

        return "|".join(parts)
