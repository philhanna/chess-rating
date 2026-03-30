"""FIDE rating adapter.

FIDE does not expose the needed profile information as a simple JSON API, so
this adapter scrapes the public profile page and extracts the visible ratings.
"""

from bs4 import BeautifulSoup

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class FIDE(RatingPort):
    """Fetch and normalize FIDE profile ratings for a single player.

    Unlike the JSON-based providers, FIDE exposes the relevant data through an
    HTML profile page. This adapter therefore performs light scraping of the
    rendered page structure and translates it into the shared output format.

    Parameters
    ----------
    player:
        FIDE profile identifier.
    http_client:
        Concrete HTTP adapter used to retrieve the profile page.
    """

    def __init__(self, player: str, http_client: HttpPort = None):
        """Initialize the adapter with a FIDE id and HTTP dependency."""
        self.player = player
        self._http_client = http_client

    def fetch(self) -> str:
        """Fetch the FIDE profile page and normalize its visible ratings.

        Returns
        -------
        str | None
            Pipe-delimited rating output on success, or ``None`` if the
            request fails or the expected profile elements are missing.
        """
        url = self.get_url()
        content = self._http_client.get(url)
        if content is None:
            return None
        # Parsing HTML is isolated in its own method so tests can focus on the
        # scraper behavior without making live network requests.
        return self.parse_content(content)

    def get_url(self) -> str:
        """Build the public FIDE profile URL for the configured player."""
        return f"https://ratings.fide.com/profile/{self.player}"

    def parse_content(self, content: str) -> str:
        """Scrape the player's name and rating categories from the HTML page.

        The method is intentionally defensive: if FIDE changes the page enough
        that the key containers disappear, it returns ``None`` instead of
        emitting misleading partial data.
        """
        soup = BeautifulSoup(content, 'html.parser')

        parts = []

        profile_div = soup.find("div", class_="profile-container")
        if not profile_div:
            return None

        player_title_h1 = profile_div.find("h1", class_="player-title")
        if not player_title_h1:
            return None
        # Preserve the display name exactly as shown on the public profile.
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
                # FIDE renders the numeric value before the category label.
                category = ps[1].get_text().strip()
                rating = ps[0].get_text().strip()
                parts.append(f"{category}={rating}")

        return "|".join(parts)
