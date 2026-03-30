"""HTTP boundary for the application.

Ports describe what the core application needs from the outside world without
coupling the rest of the codebase to a specific HTTP library.
"""

from abc import ABC, abstractmethod


class HttpPort(ABC):
    """Abstract contract for components that can issue HTTP GET requests.

    This port defines the application's minimum HTTP capability: fetching the
    body of a resource identified by URL. Infrastructure adapters implement
    this interface so the rest of the codebase can remain independent of any
    specific networking library such as ``requests``.

    Implementations are expected to translate transport-specific exceptions
    into the simple return contract documented below.
    """

    @abstractmethod
    def get(self, url: str) -> str:
        """Fetch the resource at ``url`` and return its response body.

        Parameters
        ----------
        url:
            Fully qualified URL to retrieve with an HTTP GET request.

        Returns
        -------
        str | None
            The response body as text when the request succeeds, or ``None``
            when the resource cannot be retrieved.
        """
