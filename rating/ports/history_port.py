"""Persistence boundary for recorded rating snapshots."""

from abc import ABC, abstractmethod

from rating.domain.models import NormalizedRatingProfile


class HistoryPort(ABC):
    """Abstract contract for storing normalized rating profiles."""

    @abstractmethod
    def save(self, profile: NormalizedRatingProfile) -> None:
        """Persist one normalized rating snapshot."""
