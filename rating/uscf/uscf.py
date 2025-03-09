import re
from typing import List, Optional
from bs4 import BeautifulSoup
import urllib
from rating.main import Main


class USCF(Main):
    """ Subclass for fetching USCF rating information. """

    def __init__(self, player: str):
        """ Initializes USCF with the given player name. """
        super().__init__(player)  # Call the parent class's __init__ method

    def get_url(self) -> str:
        """ Returns the URL for the USCF API stats page of the player. """
        player_encoded = urllib.parse.quote_plus(self.player)
        return f"https://www.uschess.org/datapage/player-search.php?name={player_encoded}&state=ANY"

    def parse_content(self, content: str) -> List[str]:
        """ Parses the HTML returned from the USCF API stats page. """
        soup = BeautifulSoup(content, 'html.parser')
        n_players = self._extract_player_count(soup)
        if n_players == 0:
            return []
        
        headers = self._extract_headers(soup)
        return self._extract_player_data(soup, headers, n_players)

    def _extract_player_count(self, soup: BeautifulSoup) -> int:
        """ Extracts the number of players found from the HTML. """
        pattern = re.compile(r'^Players found: (\d+)$')
        td = soup.find('td', {'colspan': '7'}, string=pattern)
        if td is None:
            return 0
        
        match = pattern.match(td.get_text().strip())
        return int(match.group(1)) if match else 0

    def _extract_headers(self, soup: BeautifulSoup) -> List[str]:
        """ Extracts column headers from the table. """
        tr = soup.find('td', {'colspan': '7'})
        if tr is None:
            return []
        tr = tr.find_parent("tr").find_next_sibling("tr")
        if tr is None:
            return []
        
        return [re.sub(r'\s+', '_', td.get_text().strip()) for td in tr.find_all("td")]

    def _extract_player_data(self, soup: BeautifulSoup, headers: List[str], n_players: int) -> List[str]:
        """ Extracts player data rows and formats them into a list of strings. """
        result_list = []
        tr = soup.find('td', {'colspan': '7'}).find_parent("tr").find_next_sibling("tr")
        
        for _ in range(n_players):
            tr = tr.find_next_sibling("tr")
            if tr is None:
                break
            
            data = [td.get_text().replace("&nbsp;", " ").strip() for td in tr.find_all("td")]
            if len(headers) != len(data):
                continue
            
            result_list.append(",".join(f"{headers[i]}={data[i]}" for i in range(len(headers))))
        
        return result_list
