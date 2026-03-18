from abc import ABC, abstractmethod


class RatingPort(ABC):
    """Port for fetching a player's chess rating. Each platform is a driven adapter."""

    @abstractmethod
    def fetch(self) -> str:
        """Fetch and return the rating string for the configured player, or None on error."""
