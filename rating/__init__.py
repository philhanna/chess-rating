# Main package for chess rating code

PACKAGE_NAME = "chess-rating"
__version__ = "0.1.0"

from .config_loader import ConfigLoader

__all__ = [
    '__version__',
    'ConfigLoader',
]
