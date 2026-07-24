"""Outbound boundary for recording normalized rating profiles."""

from abc import ABC, abstractmethod

from rating.domain.models import NormalizedRatingProfile


class ProfileLogPort(ABC):
    """Contract for persisting a fetched rating profile."""

    @abstractmethod
    def log(self, profile: NormalizedRatingProfile) -> None:
        """Record ``profile`` as a new observation."""
