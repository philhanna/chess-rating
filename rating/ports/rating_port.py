"""Rating-provider boundary for the application.

Each concrete rating adapter implements this port so the rest of the code can
ask for rating data without caring which external service is being queried.
"""

from abc import ABC, abstractmethod
from typing import Optional

from rating.domain.models import NormalizedRatingProfile


class RatingPort(ABC):
    """Abstract contract for retrieving normalized rating data for one player.

    Each external rating provider, such as Chess.com, Lichess, FIDE, or USCF,
    implements this port. The application can therefore request rating data
    through one shared interface without being coupled to provider-specific
    APIs, response formats, or scraping details.
    """

    @abstractmethod
    def fetch(self) -> Optional[NormalizedRatingProfile]:
        """Fetch and return normalized rating data for the configured player.

        Returns
        -------
        NormalizedRatingProfile | None
            A provider-independent rating profile on success, or ``None`` when
            the provider cannot supply usable data.
        """
