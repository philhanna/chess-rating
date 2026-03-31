"""US Chess Federation rating adapter.

This module talks to the USCF ratings API and returns the most recent section
rating in the normalized pipe-delimited format expected by the application.
"""

import json
import urllib

from rating.domain.models import (
    NormalizedRatingProfile,
    PlayerIdentity,
    RatingMetadata,
    build_ratings,
    normalize_rating_value,
)
from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class USCF(RatingPort):
    """Fetch and normalize USCF rating data for a single player.

    The USCF API returns a history of section records rather than a single
    headline rating. This adapter selects the newest entry from that history
    and emits the relevant fields in the shared pipe-delimited format.

    Parameters
    ----------
    player:
        USCF member identifier or search token accepted by the API.
    http_client:
        Concrete HTTP adapter used to perform outbound requests.
    """

    def __init__(self, player: str, http_client: HttpPort = None):
        """Initialize the adapter with a player id and HTTP dependency."""
        self.player = str(player)
        self._http_client = http_client

    def fetch(self) -> NormalizedRatingProfile:
        """Fetch the player's USCF history and normalize the latest rating.

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
        # Keep retrieval and JSON interpretation separate so each concern is
        # easier to test and reason about independently.
        return self.parse_content(content)

    def get_url(self) -> str:
        """Build the USCF endpoint, escaping the player identifier for URLs."""
        player_encoded = urllib.parse.quote_plus(self.player)
        return f"https://ratings-api.uschess.org/api/v1/members/{player_encoded}/sections"

    def parse_content(self, json_string: str) -> NormalizedRatingProfile:
        """Extract the latest section end date and post-rating from the payload.

        The returned string includes the player token, the section end date,
        and the most recent post-rating published in the first section record.
        """
        data = json.loads(json_string)
        # The API returns sections in newest-first order, so the first item
        # represents the latest published rating snapshot.
        items = data.get("items")
        if not items:
            return None

        latest_item = items[0]
        if not isinstance(latest_item, dict):
            return None

        date = latest_item.get("endDate")
        rating_records = latest_item.get("ratingRecords")
        if date is None or not rating_records:
            return None

        latest_rating_record = rating_records[0]
        if not isinstance(latest_rating_record, dict):
            return None

        rating = latest_rating_record.get("postRating")
        if rating is None:
            return None

        return NormalizedRatingProfile(
            provider="uscf",
            player=PlayerIdentity(id=self.player, display_name=self.player),
            ratings=build_ratings(standard=normalize_rating_value(rating)),
            metadata=RatingMetadata(as_of=date, source_url=self.get_url()),
        )
