import json
from rating.base import Base


class Lichess(Base):
    """ Subclass for fetching Lichess rating information. """

    def __init__(self, player: str):
        """ Initializes Lichess with the given player name. """
        super().__init__(player)  # Call the parent class's __init__ method

    def get_url(self) -> str:
        """ Returns the URL for the Lichess API stats page of the player. """
        return f"https://lichess.org/api/user/{self.player}"

    def parse_content(self, content: str) -> str:
        """ Parses the JSON returned from the lichess API stats page.
        It extracts a rating from each direct child elements of "perfs"
        that have a "games" child with a value greater than zero and a
        "rating" child.  The input JSON looks like this:

        {
          "id": "pehanna",
          "username": "pehanna",
          "perfs": {
            "ultraBullet": {
              "games": 2,
              "rating": 1151,
              "rd": 271,
              "prog": 0,
              "prov": true
            },
            "bullet": {
              "games": 3,
              "rating": 1046,
              "rd": 240,
              "prog": 0,
              "prov": true
            },
            ...
            etc.
            ...
        """

        # Unmarshal the content into a JSON object
        jsonobj = json.loads(content)

        # Extract ratings from all top-level "chess_xxx" objects dynamically
        filtered_perfs = {
            category: value["rating"]
            for category, value in jsonobj["perfs"].items()
            if isinstance(value, dict) and "games" in value and value["games"] > 0 and "rating" in value
        }

        # Combine the extracted ratings
        parts = []
        for category, rating in filtered_perfs.items():
            part = f"{category}={rating}"
            parts.append(part)

        # Sort by rating category name
        parts.sort()

        # Prepend the user name
        part = f"username={self.player}"
        parts.insert(0, part)

        # Join with commas
        result = ",".join(parts)

        # Return the result
        return result
