"""Normalized rating domain models.

These models define the provider-independent schema used by the adapters and
the CLI. Each rating source maps its provider-specific response into this shape
so the application can render a consistent view across services.
"""

from dataclasses import asdict, dataclass, field
from typing import Dict, Optional
import re


CANONICAL_RATING_KEYS = (
    "standard",
    "rapid",
    "blitz",
    "bullet",
    "correspondence",
)


@dataclass(frozen=True)
class PlayerIdentity:
    """Normalized player identity shared across rating providers."""

    id: str
    display_name: Optional[str] = None


@dataclass(frozen=True)
class RatingMetadata:
    """Additional information about a normalized rating profile."""

    as_of: Optional[str] = None
    source_url: Optional[str] = None


@dataclass(frozen=True)
class NormalizedRatingProfile:
    """Provider-independent rating profile returned by all adapters."""

    provider: str
    player: PlayerIdentity
    ratings: Dict[str, Optional[int]]
    extras: Dict[str, Optional[int]] = field(default_factory=dict)
    metadata: RatingMetadata = field(default_factory=RatingMetadata)

    def to_dict(self) -> dict:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)


def build_ratings(**overrides: Optional[int]) -> Dict[str, Optional[int]]:
    """Create the canonical ratings map with defaults for missing categories."""
    ratings = {key: None for key in CANONICAL_RATING_KEYS}
    ratings.update(overrides)
    return ratings


def normalize_rating_value(value) -> Optional[int]:
    """Convert provider-specific rating text into an integer or ``None``.

    Providers express missing values in different ways, such as ``None`` or
    strings like ``"Not rated"``. This helper normalizes those cases.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value

    text = str(value).strip()
    if not text or text.lower() == "not rated":
        return None

    return int(text)


def to_snake_case(value: str) -> str:
    """Convert provider-specific rating category names into snake_case."""
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    return value.strip("_").lower()
