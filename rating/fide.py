from bs4 import BeautifulSoup
from rating.base import Base


class FIDE(Base):
    """ Subclass for fetching FIDE rating information. """

    def __init__(self, player: str):
        """ Initializes FIDE with the given player name. """
        super().__init__(player)

    def get_url(self) -> str:
        """ Returns the URL for the FIDE page of the player. """
        return f"https://ratings.fide.com/profile/{self.player}"

    def parse_content(self, content: str) -> str:
        """ Parses the HTML returned from the FIDE page. """
        soup = BeautifulSoup(content, 'html.parser')
        
        # For debugging only:
        html = soup.prettify()
        _ = html
        
        parts = []
                
        # Get the profile container
        profile_div = soup.find("div", class_="profile-container")
        if not profile_div:
            return None
        
        # Get the user name
        player_title_h1 = profile_div.find("h1", class_="player-title")
        if not player_title_h1:
            return None        
        text = f'Username="{player_title_h1.get_text().strip()}"'
        parts.append(text)
        
        # Get the profile section, which has the ratings
        profile_section_div = soup.find("div", class_="profile-section")
        assert profile_section_div is not None
        
        # The games begin in the profile games div
        profile_games_div = profile_section_div.find("div", class_="profile-games")
        if profile_games_div:
            divs = profile_games_div.find_all("div", recursive=False)
            for div in divs:
                ps = div.find_all("p")
                assert ps is not None
                assert len(ps) >= 2, f'Expected 2 <p>, found {len(ps)}'
                ps1 = ps[0] # rating
                ps2 = ps[1] # category
                category = ps2.get_text().strip()
                rating = ps1.get_text().strip()
                part = "=".join([category, rating])
                parts.append(part)
        
        result = "|".join(parts)
        return result