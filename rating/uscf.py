import json
import urllib
from rating.base import Base


class USCF(Base):
    """Subclass for fetching USCF rating information."""

    def __init__(self, player: str):
        """Initializes USCF with the given player name."""
        super().__init__(player)  # Call the parent class's __init__ method

    def get_url(self) -> str:
        """Returns the URL for the USCF API page for the latest
        tournament for this player"""

        self.player = str(self.player)
        player_encoded = urllib.parse.quote_plus(self.player)
        url = (
            f"https://ratings-api.uschess.org/api/v1/members/{player_encoded}/sections"
        )
        return url

    def parse_content(self, json_string: str) -> str:
       # print(f"DEBUG: json={json_string}")
        data = json.loads(json_string)

        date = data["items"][0]["endDate"]
        rating = data["items"][0]["ratingRecords"][0]["postRating"]

        result = f"player={self.player}|date={date}|rating={rating}"
        return result
