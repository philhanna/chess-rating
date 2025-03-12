import json
from typing import List
from rating.main import Main


class ChessCom(Main):
    """ Subclass for fetching Chess.com rating information. """

    def __init__(self, player: str):
        """ Initializes ChessCom with the given player name. """
        super().__init__(player)  # Call the parent class's __init__ method

    def get_url(self) -> str:
        """ Returns the URL for the chess.com API stats page of the player. """
        return f"https://api.chess.com/pub/player/{self.player}/stats"

    def parse_content(self, content: str) -> str:
        """ Parses the JSON returned from the chess.com API stats page.
        It extracts a rating from each top-level element with a name like
        "chess_something", with a prefix of "chess_" and a suffix of something.
        The rating is returned.
        """
        
        # Unmarshal the content into a JSON object
        parsed_data = json.loads(content)
        
        # Extract ratings from all top-level "chess_xxx" objects dynamically
        ratings = {}
        for key, value in parsed_data.items():
            if key.startswith("chess_") and isinstance(value, dict) and "last" in value:
                ratings[key] = value["last"].get("rating", "N/A")

        # Combine the extracted ratings
        parts = []
        for category, rating in ratings.items():
            suffix = category.split("_", 1)[1] 
            part = f"{suffix}={rating}"
            parts.append(part)
        
        # Sort by rating category name
        parts.sort()
        
        # Prepend the user name
        part = f"username={self.player}"
        parts.insert(0, part)
        
        # Join with commas
        result = ",".join(parts)

        # Return the list
        return result