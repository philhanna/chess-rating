"""Helpers for locating and loading the application's dotenv configuration.

The CLI uses this module to find a per-user ``.env`` file containing default
player identifiers for each supported chess platform. Callers may either supply
an explicit filename or let :class:`ConfigLoader` resolve the platform-specific
default location.
"""

import os
from dotenv import dotenv_values
from platformdirs import user_config_dir
from rating import PACKAGE_NAME


class ConfigLoader:
    """Load chess-rating configuration from dotenv settings.

    The loaded mapping is exposed through :attr:`config`, while the resolved
    path is kept in :attr:`filename` for callers that need to inspect where the
    configuration came from.

    Args:
        filename: Optional explicit path to a dotenv file. When omitted,
            the loader uses ``platformdirs.user_config_dir`` together with the
            package name to locate the default ``.env`` file for the
            current user.
    """

    def __init__(self, filename=None):
        """Resolve the config path and immediately load its contents."""
        self.filename = filename or self._get_default_filename()
        self.config = self._load_config()

    def _get_default_filename(self):
        """Return the default per-user configuration filename.

        Returns:
            The absolute path to ``.env`` inside the user-specific
            configuration directory for this application.
        """
        # ``platformdirs`` chooses the correct OS-specific config directory
        # (for example under ``~/.config`` on Linux) so the rest of the code
        # does not need to care about platform differences.
        filename = os.path.join(user_config_dir(PACKAGE_NAME), ".env")
        return filename

    def _load_config(self):
        """Read and parse the dotenv configuration file.

        Returns:
            A nested mapping with per-platform default usernames.

        Raises:
            FileNotFoundError: If ``self.filename`` does not exist.
        """
        if not os.path.exists(self.filename):
            raise FileNotFoundError(self.filename)

        env = dotenv_values(self.filename)
        return {
            "lichess": {"defaultUser": env.get("LICHESS_DEFAULT_USER")},
            "USCF": {"defaultUser": env.get("USCF_DEFAULT_USER")},
            "Chess": {"defaultUser": env.get("CHESS_DEFAULT_USER")},
            "FIDE": {"defaultUser": env.get("FIDE_DEFAULT_USER")},
        }
