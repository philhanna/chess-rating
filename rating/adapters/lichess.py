"""Lichess rating adapter.

This module translates the Lichess user API response into the compact
pipe-delimited format used by the rest of the application.
"""

import json

from rating.domain.models import (
    NormalizedRatingProfile,
    PlayerIdentity,
    RatingMetadata,
    build_ratings,
    normalize_rating_value,
    to_snake_case,
)
from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class Lichess(RatingPort):
    """Fetch and normalize Lichess ratings for a single player.

    Lichess exposes rating data through a JSON profile endpoint containing a
    ``perfs`` object. This adapter filters that object down to active rating
    categories and converts the result into the application's shared string
    representation.

    Parameters
    ----------
    player:
        Lichess username to query.
    http_client:
        Concrete HTTP adapter used to perform outbound requests.
    """

    def __init__(self, player: str, http_client: HttpPort = None):
        """Initialize the adapter with a username and HTTP dependency."""
        self.player = player
        self._http_client = http_client

    def fetch(self) -> NormalizedRatingProfile:
        """Fetch and normalize the configured player's Lichess ratings.

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
        # Delegate the provider-specific data shaping to a dedicated method to
        # keep fetch orchestration simple and predictable.
        return self.parse_content(content)

    def get_url(self) -> str:
        """Build the Lichess API URL for the configured player."""
        return f"https://lichess.org/api/user/{self.player}"

    def parse_content(self, content: str) -> NormalizedRatingProfile:
        """Extract active performance ratings from the Lichess JSON payload.

        Only performance categories with at least one recorded game are kept,
        which avoids including empty placeholders returned by the API.
        """
        jsonobj = json.loads(content)

        # Lichess returns many performance buckets; keep only categories that
        # actually have games played and a rating value.
        filtered_perfs = {
            category: value["rating"]
            for category, value in jsonobj["perfs"].items()
            if isinstance(value, dict) and "games" in value and value["games"] > 0 and "rating" in value
        }

        ratings = build_ratings(
            standard=normalize_rating_value(filtered_perfs.get("classical")),
            rapid=normalize_rating_value(filtered_perfs.get("rapid")),
            blitz=normalize_rating_value(filtered_perfs.get("blitz")),
            bullet=normalize_rating_value(filtered_perfs.get("bullet")),
            correspondence=normalize_rating_value(filtered_perfs.get("correspondence")),
        )
        extras = {
            to_snake_case(category): normalize_rating_value(value)
            for category, value in filtered_perfs.items()
            if category not in {"classical", "rapid", "blitz", "bullet", "correspondence"}
        }

        return NormalizedRatingProfile(
            provider="lichess",
            player=PlayerIdentity(
                id=jsonobj.get("id", self.player),
                display_name=jsonobj.get("username", self.player),
            ),
            ratings=ratings,
            extras=extras,
            metadata=RatingMetadata(source_url=self.get_url()),
        )
