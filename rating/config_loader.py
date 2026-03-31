"""Helpers for locating and loading the application's YAML configuration.

The CLI uses this module to find a per-user config file containing default
player identifiers for each supported chess platform. Callers may either supply
an explicit filename or let :class:`ConfigLoader` resolve the platform-specific
default location.
"""

import os
import yaml
from platformdirs import user_config_dir, user_data_dir
from rating import PACKAGE_NAME


class ConfigLoader:
    """Load chess-rating configuration from YAML.

    The loaded mapping is exposed through :attr:`config`, while the resolved
    path is kept in :attr:`filename` for callers that need to inspect where the
    configuration came from.

    Args:
        filename: Optional explicit path to a YAML config file. When omitted,
            the loader uses ``platformdirs.user_config_dir`` together with the
            package name to locate the default ``config.yaml`` file for the
            current user.
    """

    def __init__(self, filename=None):
        """Resolve the config path and immediately load its contents."""
        self.filename = filename or self._get_default_filename()
        self.config = self._load_config()

    def _get_default_filename(self):
        """Return the default per-user configuration filename.

        Returns:
            The absolute path to ``config.yaml`` inside the user-specific
            configuration directory for this application.
        """
        # ``platformdirs`` chooses the correct OS-specific config directory
        # (for example under ``~/.config`` on Linux) so the rest of the code
        # does not need to care about platform differences.
        filename = os.path.join(user_config_dir(PACKAGE_NAME), "config.yaml")
        return filename

    def _get_default_database_path(self):
        """Return the default path for the history SQLite database."""
        return os.path.join(user_data_dir(PACKAGE_NAME), "chess-rating.db")

    def _apply_defaults(self, config):
        """Ensure expected configuration keys exist with stable defaults."""
        database_config = config.setdefault("database", {})
        database_config.setdefault("path", self._get_default_database_path())
        database_config.setdefault("enabled", True)
        return config

    def _load_config(self):
        """Read and parse the YAML configuration file.

        Returns:
            The Python object produced by ``yaml.safe_load``. In practice this
            project expects a mapping with per-platform default usernames.

        Raises:
            FileNotFoundError: If ``self.filename`` does not exist.
            yaml.YAMLError: If the file exists but contains invalid YAML.
        """
        # Let file and YAML parsing errors propagate naturally so the CLI or
        # tests can surface a clear failure instead of silently guessing.
        with open(self.filename, "r") as fp:
            config = yaml.safe_load(fp) or {}

        return self._apply_defaults(config)

    def set_database_enabled(self, enabled: bool) -> None:
        """Persist the database logging setting while preserving comments."""
        from ruamel.yaml import YAML
        from ruamel.yaml.comments import CommentedMap

        yaml_rt = YAML()
        yaml_rt.preserve_quotes = True

        with open(self.filename, "r") as fp:
            config = yaml_rt.load(fp) or CommentedMap()

        if not isinstance(config, dict):
            raise TypeError("Config file must contain a mapping at the top level")

        database_config = config.get("database")
        if database_config is None:
            database_config = CommentedMap()
            config["database"] = database_config
        elif not isinstance(database_config, dict):
            raise TypeError("The 'database' config entry must be a mapping")

        if "path" not in database_config:
            database_config["path"] = self._get_default_database_path()
        database_config["enabled"] = bool(enabled)

        with open(self.filename, "w") as fp:
            yaml_rt.dump(config, fp)

        with open(self.filename, "r") as fp:
            self.config = self._apply_defaults(yaml.safe_load(fp) or {})
