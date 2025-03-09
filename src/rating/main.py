from abc import ABC, abstractmethod
import sys
from typing import List

import requests


class Main(ABC):
    """ Main is an abstract base class for running the chess rating
    application.  There should be subclasses for the USCF, Lichess,
    chess.com, and FIDE rating platforms.

    This class uses the Template design pattern:
    https://en.wikipedia.org/wiki/Template_method_pattern.
    It defines the outline of the operation but relies on subclasses
    to provide necessary implementations of the details of their
    particular platform.

    It also provides the implementation of functions common to all
    subclasses, like the HTTP "get" method.
    """

    def __init__(self, player: str):
        """ Creates a new Main """

        # Store the player ID or name
        self.player: str = player

    # ------------------------------------------------------------------
    #   Common methods used by all subclasses
    # ------------------------------------------------------------------
    def run(self):
        """
        Fetches and processes rating information from the specified rating platform.

        This method performs the following steps:
        
        1. Constructs the URL for fetching rating data using the `get_url` method, 
        which must be implemented by each subclass.
        
        2. Retrieves the content from the URL using the `get` method. If an error 
        occurs, the method prints an error message and returns early.
        
        3. Parses the retrieved content using the `parse_content` method, which 
        processes the HTML or JSON data according to the platform’s format. 
        The output is expected to be a list of strings representing rating 
        information or None if an error occurs.
        
        4. If parsing is successful, prints the extracted rating(s) to the console.

        """
        
        url = self.get_url()
        
        content = self.get(url)
        if not content:
            return
        
        output: List[str] = self.parse_content(content)
        if not output:
            return
        
        print("\n".join(output))

    def get(self, url: str) -> str:
        """
        Sends an HTTP GET request to the specified URL and returns the response body as a string.

        Args:
            url (str): The URL to send the GET request to.

        Returns:
            str: The response content as a string, or None, if an error occurred

        Raises:
            RuntimeError: If the request encounters an error (e.g., network issues, HTTP errors).
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            errmsg = f"Error: {e}"
            print(errmsg, file=sys.stderr)
            return None

    # ------------------------------------------------------------------
    #   Abstract methods implemented by all subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def get_url(self):
        """ Returns the URL that get the ratings page. Must be implemented
        by subclasses. """

        pass

    @abstractmethod
    def parse_content(self, content: str) -> List[str]:
        """ Reads the content returned by the HTTP get() and extracts
        the rating or ratings from it.  Must be implemented by
        subclasses. """

        pass
