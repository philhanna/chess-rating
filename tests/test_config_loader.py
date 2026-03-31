import os
import textwrap

import pytest

from rating import ConfigLoader
from tests import PROJECT_ROOT


def test_load_config_from_file():
    config_file = os.path.join(PROJECT_ROOT, "sample_config.yaml")
    loader = ConfigLoader(config_file)
    assert loader.config.get("lichess") is not None
    assert loader.config["lichess"]["defaultUser"] == "pehanna"
    assert loader.config["database"]["enabled"] is True


def test_load_config_from_default_file():
    loader = ConfigLoader()
    assert loader.config.get("Chess") is not None
    assert loader.config["Chess"]["defaultUser"] == "pehanna7"


def test_missing_file_raises_error(tmp_path):
    missing_file = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        ConfigLoader(str(missing_file))


def test_database_enabled_defaults_to_true_when_omitted(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        textwrap.dedent(
            """
            lichess:
              defaultUser: pehanna

            database:
              path: /tmp/test-history.sqlite3
            """
        ).lstrip()
    )

    loader = ConfigLoader(str(config_file))

    assert loader.config["database"]["enabled"] is True


def test_set_database_enabled_preserves_comments(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        textwrap.dedent(
            """
            # top-level comment
            lichess:
              # keep this comment
              defaultUser: pehanna

            database:
              # database path comment
              path: /tmp/test-history.sqlite3
              enabled: true  # inline enabled comment
            """
        ).lstrip()
    )

    loader = ConfigLoader(str(config_file))

    loader.set_database_enabled(False)

    updated = config_file.read_text()
    assert "# top-level comment" in updated
    assert "# keep this comment" in updated
    assert "# database path comment" in updated
    assert "# inline enabled comment" in updated
    assert "enabled: false" in updated
    assert loader.config["database"]["enabled"] is False
