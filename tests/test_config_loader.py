import os
from pathlib import Path

import pytest

from rating import ConfigLoader
from rating import config_loader
from tests import PROJECT_ROOT


def test_load_config_from_file():
    config_file = os.path.join(PROJECT_ROOT, "sample.env")
    loader = ConfigLoader(config_file)
    assert loader.config.get("lichess") is not None
    assert loader.config["lichess"]["defaultUser"] == "pehanna"


def test_load_config_from_default_file(tmp_path, monkeypatch):
    config_dir = tmp_path / "chess-rating"
    config_dir.mkdir()
    config_path = config_dir / ".env"
    config_path.write_text(
        "CHESS_DEFAULT_USER=pehanna7\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(config_loader, "user_config_dir", lambda _package_name: str(config_dir))

    loader = ConfigLoader()
    assert loader.config.get("Chess") is not None
    assert loader.config["Chess"]["defaultUser"] == "pehanna7"
    assert Path(loader.filename) == config_path


def test_missing_file_raises_error(tmp_path):
    missing_file = tmp_path / "nonexistent.env"
    with pytest.raises(FileNotFoundError):
        ConfigLoader(str(missing_file))
