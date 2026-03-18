import json
import urllib

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class USCF(RatingPort):
    """Driven adapter: fetches USCF rating information."""

    def __init__(self, player: str, http_client: HttpPort = None):
        self.player = str(player)
        self._http_client = http_client

    def fetch(self) -> str:
        url = self.get_url()
        content = self._http_client.get(url)
        if content is None:
            return None
        return self.parse_content(content)

    def get_url(self) -> str:
        player_encoded = urllib.parse.quote_plus(self.player)
        return f"https://ratings-api.uschess.org/api/v1/members/{player_encoded}/sections"

    def parse_content(self, json_string: str) -> str:
        data = json.loads(json_string)
        date = data["items"][0]["endDate"]
        rating = data["items"][0]["ratingRecords"][0]["postRating"]
        return f"player={self.player}|date={date}|rating={rating}"
