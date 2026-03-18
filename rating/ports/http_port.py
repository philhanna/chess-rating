from abc import ABC, abstractmethod


class HttpPort(ABC):
    """Port for making HTTP GET requests. Implementations are infrastructure adapters."""

    @abstractmethod
    def get(self, url: str) -> str:
        """Send a GET request and return the response body, or None on error."""
