import json

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class Lichess(RatingPort):
    """Driven adapter: fetches Lichess rating information."""

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
        return f"https://lichess.org/api/user/{self.player}"

    def parse_content(self, content: str) -> str:
        jsonobj = json.loads(content)

        filtered_perfs = {
            category: value["rating"]
            for category, value in jsonobj["perfs"].items()
            if isinstance(value, dict) and "games" in value and value["games"] > 0 and "rating" in value
        }

        parts = [f"{category}={rating}" for category, rating in filtered_perfs.items()]
        parts.sort()
        parts.insert(0, f"username={self.player}")

        return "|".join(parts)
