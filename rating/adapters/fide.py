"""FIDE rating adapter.

FIDE does not expose the needed profile information as a simple JSON API, so
this adapter scrapes the public profile page and extracts the visible ratings.
"""

from bs4 import BeautifulSoup

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class FIDE(RatingPort):
    """Fetch and normalize FIDE profile ratings for a single player."""

    def __init__(self, player: str, http_client: HttpPort = None):
        """Store the player identifier and injected HTTP client."""
        self.player = player
        self._http_client = http_client

    def fetch(self) -> str:
        """Request the FIDE profile page and parse visible ratings from it."""
        url = self.get_url()
        content = self._http_client.get(url)
        if content is None:
            return None
        return self.parse_content(content)

    def get_url(self) -> str:
        """Build the public FIDE profile URL for the configured player."""
        return f"https://ratings.fide.com/profile/{self.player}"

    def parse_content(self, content: str) -> str:
        """Scrape the player's name and rating categories from the HTML page."""
        soup = BeautifulSoup(content, 'html.parser')

        parts = []

        profile_div = soup.find("div", class_="profile-container")
        if not profile_div:
            return None

        player_title_h1 = profile_div.find("h1", class_="player-title")
        if not player_title_h1:
            return None
        parts.append(f'Username="{player_title_h1.get_text().strip()}"')

        profile_section_div = soup.find("div", class_="profile-section")
        assert profile_section_div is not None

        profile_games_div = profile_section_div.find("div", class_="profile-games")
        if profile_games_div:
            # Each direct child div represents one rating category card whose
            # first two <p> elements contain the numeric rating and label.
            divs = profile_games_div.find_all("div", recursive=False)
            for div in divs:
                ps = div.find_all("p")
                assert ps is not None
                assert len(ps) >= 2, f'Expected 2 <p>, found {len(ps)}'
                category = ps[1].get_text().strip()
                rating = ps[0].get_text().strip()
                parts.append(f"{category}={rating}")

        return "|".join(parts)
