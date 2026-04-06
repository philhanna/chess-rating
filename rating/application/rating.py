"""Main CLI orchestration for the chess rating application.

This module acts as the application's composition root. It wires together
argument parsing, configuration lookup, HTTP access, and the platform-specific
rating adapters.
"""

import argparse
import json
import sys
from importlib.metadata import version

from rating import PACKAGE_NAME
from rating.adapters.chesscom import ChessCom
from rating.adapters.fide import FIDE
from rating.adapters.lichess import Lichess
from rating.adapters.requests_http import RequestsHttpAdapter
from rating.adapters.uscf import USCF
from rating.config_loader import ConfigLoader
from rating.domain.models import CANONICAL_RATING_KEYS, NormalizedRatingProfile


def _format_rating_value(value) -> str:
    """Render a normalized rating value for plain-text CLI output."""
    return "Not rated" if value is None else str(value)


def _to_json(profile: NormalizedRatingProfile) -> str:
    """Convert a normalized rating profile into formatted JSON."""
    return json.dumps(profile.to_dict(), indent=4)


def _to_pipe(profile: NormalizedRatingProfile) -> str:
    """Render a normalized rating profile in the CLI's plain-text format."""
    parts = [
        f"provider={profile.provider}",
        f"player_id={profile.player.id}",
    ]
    if profile.player.display_name is not None:
        parts.append(f"display_name={profile.player.display_name}")

    for key in CANONICAL_RATING_KEYS:
        value = profile.ratings.get(key)
        if value is None:
            continue
        parts.append(f"{key}={_format_rating_value(value)}")

    for key in sorted(profile.extras):
        parts.append(f"{key}={_format_rating_value(profile.extras[key])}")

    if profile.metadata.as_of is not None:
        parts.append(f"as_of={profile.metadata.as_of}")

    return "\n".join(parts)


def _build_fetch_parser() -> argparse.ArgumentParser:
    """Create the parser for normal rating-fetch commands."""
    parser = argparse.ArgumentParser(
        prog="rating",
        description=(
            "Fetches and prints a players's chess rating from USCF, FIDE, "
            "Lichess, or Chess.com.\n\n"
            "Special commands:\n"
            "  rating config\n"
            "    Print the active configuration file path and its contents."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {version(PACKAGE_NAME)}",
        help="Show the project version and exit",
    )
    parser.add_argument("player", nargs="?", default=None, help="The player's ID or name.")
    parser.add_argument("-j", "--json", action="store_true", help="Create JSON output")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--uscf", action="store_true", help="Use USCF platform")
    group.add_argument("-l", "--lichess", action="store_true", help="Use Lichess platform")
    group.add_argument("-c", "--chess", action="store_true", help="Use chess.com platform")
    group.add_argument("-f", "--fide", action="store_true", help="Use FIDE platform")
    return parser


def _build_config_parser() -> argparse.ArgumentParser:
    """Create the parser for configuration inspection commands."""
    return argparse.ArgumentParser(
        prog="rating config",
        description="Show the active configuration file and its contents.",
    )


def _handle_config_command(argv: list[str], loader: ConfigLoader) -> None:
    """Print the active config filename and its raw contents, then exit."""
    _build_config_parser().parse_args(argv)
    print(loader.filename)
    with open(loader.filename, "r") as fp:
        contents = fp.read()
    print(contents, end="" if not contents or contents.endswith("\n") else "\n")


def main() -> None:
    """Run the CLI and print either rating data or a not-found message.

    Flow:

    1. Load the local configuration file so each platform can supply a default
       user when the caller omits the positional ``player`` argument.
    2. Parse the CLI options and require exactly one ratings platform.
    3. Create the appropriate adapter and ask it to fetch the rating data.
    4. Print either the raw adapter output, JSON-converted output, or a helpful
       "not found" message when the adapter returns no data.
    """
    loader = ConfigLoader()
    config = loader.config
    argv = sys.argv[1:]
    if argv and argv[0] == "config":
        _handle_config_command(argv[1:], loader)
        return

    args = _build_fetch_parser().parse_args(argv)

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
    else:
        player = args.player or config["USCF"]["defaultUser"]
        app = USCF(player, http_client)

    profile = app.fetch()
    if not profile:
        print(f'No ratings found for "{player}"')
    else:
        if args.json:
            print(_to_json(profile))
        else:
            print(_to_pipe(profile))


if __name__ == "__main__":
    main()