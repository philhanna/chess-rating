from bs4 import BeautifulSoup

from rating.ports.http_port import HttpPort
from rating.ports.rating_port import RatingPort


class FIDE(RatingPort):
    """Driven adapter: fetches FIDE rating information."""

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
        return f"https://ratings.fide.com/profile/{self.player}"

    def parse_content(self, content: str) -> str:
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
            divs = profile_games_div.find_all("div", recursive=False)
            for div in divs:
                ps = div.find_all("p")
                assert ps is not None
                assert len(ps) >= 2, f'Expected 2 <p>, found {len(ps)}'
                category = ps[1].get_text().strip()
                rating = ps[0].get_text().strip()
                parts.append(f"{category}={rating}")

        return "|".join(parts)
