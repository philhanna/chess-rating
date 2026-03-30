#! /usr/bin/python
"""Command-line entry point for the chess rating application.

This module wires together argument parsing, configuration lookup, HTTP access,
and the platform-specific rating adapters. Running ``python -m rating`` enters
here.

The CLI accepts either an explicit player identifier on the command line or, if
the player argument is omitted, falls back to a platform-specific default user
loaded from the local configuration file.
"""

import argparse
import json

from rating import __version__
from rating.adapters.chesscom import ChessCom
from rating.adapters.fide import FIDE
from rating.adapters.lichess import Lichess
from rating.adapters.requests_http import RequestsHttpAdapter
from rating.adapters.uscf import USCF
from rating.config_loader import ConfigLoader


def _to_json(s: str) -> str:
    """Convert the legacy pipe-delimited adapter output into formatted JSON.

    The platform adapters currently return strings in a compact
    ``key=value|key=value`` format. When the ``--json`` flag is used, the CLI
    translates that output into a JSON object for easier downstream
    consumption.

    Args:
        s: Adapter output formatted as pipe-separated ``key=value`` pairs.

    Returns:
        A pretty-printed JSON string containing the same key/value data.
    """
    d = {}
    for part in s.split("|"):
        # The adapter output may already contain quoted fragments, so the CLI
        # strips those before splitting the field into key and value.
        part = part.replace('"', "")
        k, v = part.split("=")
        d[k] = v
    return json.dumps(d, indent=4)


def main() -> None:
    """Run the CLI and print either rating data or a not-found message.

    Flow:

    1. Load the local configuration file so each platform can supply a default
       user when the caller omits the positional ``player`` argument.
    2. Parse the CLI options and select exactly one ratings platform, defaulting
       to USCF when no platform flag is supplied.
    3. Create the appropriate adapter and ask it to fetch the rating data.
    4. Print either the raw adapter output, JSON-converted output, or a helpful
       "not found" message when the adapter returns no data.
    """
    loader = ConfigLoader()
    config = loader.config

    parser = argparse.ArgumentParser(
        description="Fetches and prints a players's chess rating from USCF, FIDE, Lichess, or Chess.com."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the project version and exit",
    )
    parser.add_argument("player", nargs="?", default=None, help="The player's ID or name.")
    parser.add_argument("-j", "--json", action="store_true", help="Create JSON output")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-u", "--uscf", action="store_true", help="Use USCF platform")
    group.add_argument("-l", "--lichess", action="store_true", help="Use Lichess platform")
    group.add_argument("-c", "--chess", action="store_true", help="Use chess.com platform")
    group.add_argument("-f", "--fide", action="store_true", help="Use FIDE platform")

    args = parser.parse_args()

    # The HTTP adapter is shared by all platform clients. Keeping the concrete
    # transport creation here lets the individual rating adapters stay focused
    # on parsing their respective services.
    http_client = RequestsHttpAdapter()

    # Each branch picks a player identifier from either the command line or the
    # per-platform default stored in the config file, then constructs the
    # matching adapter.
    if args.lichess:
        player = args.player or config["lichess"]["defaultUser"]
        app = Lichess(player, http_client)
    elif args.chess:
        player = args.player or config["Chess"]["defaultUser"]
        app = ChessCom(player, http_client)
    elif args.fide:
        player = args.player or config["FIDE"]["defaultUser"]
        app = FIDE(player, http_client)
    else:  # USCF is the default when no explicit platform flag is given.
        player = args.player or config["USCF"]["defaultUser"]
        app = USCF(player, http_client)

    output = app.fetch()
    if not output:
        print(f'No ratings found for "{player}"')
    else:
        # The adapters return plain text by default; JSON conversion is an
        # output-formatting concern handled entirely at the CLI layer.
        if args.json:
            output = _to_json(output)
        print(output)


if __name__ == "__main__":
    main()
