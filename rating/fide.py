import sys
from typing import List

from bs4 import BeautifulSoup
from rating.main import Main


class FIDE(Main):
    """ Subclass for fetching FIDE rating information. """

    def __init__(self, player: str):
        """ Initializes FIDE with the given player name. """
        super().__init__(player)

    def get_url(self) -> str:
        """ Returns the URL for the FIDE page of the player. """
        return f"https://ratings.fide.com/profile/{self.player}"

    def parse_content(self, content: str) -> List[str]:
        """ Parses the HTML returned from the FIDE page. """
        soup = BeautifulSoup(content, 'html.parser')
        
        # For debugging only:
        html = soup.prettify()
        _ = html
        
        # Get the profile container
        profile_div = soup.find("div", class_="profile-container")
        if not profile_div:
            return None
        
        # Get the user name
        player_title_h1 = profile_div.find("h1", class_="player-title")
        if not player_title_h1:
            return None
        
        text = player_title_h1.get_text().strip()
        results = [text]
        return results