import os
import pytest
from rating import ConfigLoader
from tests import PROJECT_ROOT

def test_load_config_from_file():
    config_file = os.path.join(PROJECT_ROOT, "sample_config.yaml")
    loader = ConfigLoader(config_file)
    assert loader.config.get("lichess") is not None
    assert loader.config["lichess"]["defaultUser"] == "pehanna"

def test_load_config_from_default_file():
    loader = ConfigLoader()
    assert loader.config.get("Chess") is not None
    assert loader.config["Chess"]["defaultUser"] == "pehanna7"

def test_missing_file_raises_error(tmp_path):
    missing_file = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        ConfigLoader(str(missing_file))
