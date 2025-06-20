import os
import yaml
from platformdirs import user_config_dir
from rating import PACKAGE_NAME

class ConfigLoader:
    def __init__(self, filename=None):
        self.filename = filename or self._get_default_filename()
        self.config = self._load_config()
        
    def _get_default_filename(self):
        filename = os.path.join(user_config_dir(PACKAGE_NAME), "config.yaml")
        return filename
    
    def _load_config(self):
        with open(self.filename, "r") as fp:
            return yaml.safe_load(fp)
