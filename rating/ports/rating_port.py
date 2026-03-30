"""Rating-provider boundary for the application.

Each concrete rating adapter implements this port so the rest of the code can
ask for rating data without caring which external service is being queried.
"""

from abc import ABC, abstractmethod


class RatingPort(ABC):
    """Abstract contract for retrieving normalized rating data for one player."""

    @abstractmethod
    def fetch(self) -> str:
        """Return normalized rating output for the configured player, or ``None`` on error."""
