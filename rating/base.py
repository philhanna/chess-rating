from abc import ABC, abstractmethod

from rating import http_get
from rating import ConfigLoader


class Base(ABC):
    """ Base is an abstract base class for running the chess rating
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

    def __init__(self, player: str = None):
        """ Creates a new Base """
        
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
        assert url is not None
        content = http_get(url)
        assert content is not None
        output: str = self.parse_content(content)
        if not output:
            print(f'No ratings found for "{self.player}"')
            return
        
        print(output)

    # ------------------------------------------------------------------
    #   Abstract methods implemented by all subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def get_url(self):
        """ Returns the URL that get the ratings page. Must be implemented
        by subclasses. """

    @abstractmethod
    def parse_content(self, content: str) -> str:
        """ Reads the content returned by the HTTP get() and extracts
        the rating or ratings from it.  Must be implemented by
        subclasses. """
