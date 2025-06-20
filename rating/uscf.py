import re
from typing import List
from bs4 import BeautifulSoup
import urllib
from rating.base import Base


class USCF(Base):
    """ Subclass for fetching USCF rating information. """

    def __init__(self, player: str):
        """ Initializes USCF with the given player name. """
        super().__init__(player)  # Call the parent class's __init__ method

    def get_url(self) -> str:
        """ Returns the URL for the USCF API stats page of the player. """
        self.player = str(self.player)
        player_encoded = urllib.parse.quote_plus(self.player)
        return f"https://www.uschess.org/datapage/player-search.php?name={player_encoded}&state=ANY"

    def parse_content(self, content: str) -> str:
        """ Parses the HTML returned from the USCF API stats page. """
        soup = BeautifulSoup(content, 'html.parser')
        n_players = USCF.extract_player_count(soup)
        if n_players == 0:
            return ""
        
        headers = USCF.extract_headers(soup)
        result = USCF.extract_player_data(soup, headers, n_players)
        return result
    
    
    #   ----------------------------------------------------------------
    #   Static methods (split here for ease of unit testing)
    #   ----------------------------------------------------------------

    @staticmethod
    def extract_player_count(soup: BeautifulSoup) -> int:
        """ Extracts the number of players found from the HTML. """
        pattern = re.compile(r'^Players found: (\d+)$')
        td = soup.find('td', {'colspan': '7'}, string=pattern)
        if td is None:
            return 0
        
        match = pattern.match(td.get_text().strip())
        return int(match.group(1)) if match else 0

    @staticmethod
    def extract_headers(soup: BeautifulSoup) -> List[str]:
        """ Extracts column headers from the table. """
        td = soup.find('td', {'colspan': '7'})
        if td is None:
            return []
        tr = td.find_parent("tr").find_next_sibling("tr")
        if tr is None:
            return []
        
        return [re.sub(r'\s+', '_', td.get_text().strip()) for td in tr.find_all("td")]

    @staticmethod
    def extract_player_data(soup: BeautifulSoup, headers: List[str], n_players: int) -> str:
        """ Extracts player data rows and formats them into a list of strings. """
        result_list = []
        tr = soup.find('td', {'colspan': '7'}).find_parent("tr").find_next_sibling("tr")
        
        for _ in range(n_players):
            tr = tr.find_next_sibling("tr")
            if tr is None:
                break
            
            data: List[str] = []
            for td in tr.find_all("td"):
                line = td.get_text()
                line = line.replace("&nbsp;", " ").strip()
                data.append(line)
                
            if len(headers) != len(data):
                continue
            
            result = []
            for i in range(len(headers)):
                # Skip any inapplicable categories
                if data[i] == "Unrated":
                    continue
                pair = f"{headers[i]}={data[i]}"
                result.append(pair)

            joined_result = ",".join(result)
            result_list.append(joined_result)

        result = "\n".join(result_list)
        return result
