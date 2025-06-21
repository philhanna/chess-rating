# Main package for chess rating code
import json
import sys
import requests

PACKAGE_NAME = "chess-rating"

def http_get(url: str) -> str:
    """
    Sends an HTTP GET request to the specified URL and returns the response body as a string.

    Args:
        url (str): The URL to send the GET request to.

    Returns:
        str: The response content as a string, or None, if an error occurred

    Raises:
        RuntimeError: If the request encounters an error (e.g., network issues, HTTP errors).
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        errmsg = f"Error: {e}"
        print(errmsg, file=sys.stderr)
        return None

def toJson(s: str) -> str:
    d = dict()
    parts = s.split("|")
    for part in parts:
        part = part.replace('"', '')
        k, v = part.split("=")
        d[k] = v
        
    jsonstr = json.dumps(d, indent=4)
    return jsonstr
    
from .config_loader import ConfigLoader

__all__ = [
    'http_get',
    'ConfigLoader',
    'toJson',
]
