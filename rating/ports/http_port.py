"""HTTP boundary for the application.

Ports describe what the core application needs from the outside world without
coupling the rest of the codebase to a specific HTTP library.
"""

from abc import ABC, abstractmethod


class HttpPort(ABC):
    """Abstract contract for components that can issue HTTP GET requests."""

    @abstractmethod
    def get(self, url: str) -> str:
        """Return the response body for ``url`` or ``None`` when retrieval fails."""
