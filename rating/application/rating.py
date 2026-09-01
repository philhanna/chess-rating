"""Main CLI orchestration for the chess rating application.

This module acts as the application's composition root. It wires together
argument parsing, configuration lookup, HTTP access, and the platform-specific
rating adapters.
"""

import argparse
import json
import os
import sys
import tempfile
from typing import Optional

from rating.adapters.chesscom import ChessCom
from rating.adapters.fide import FIDE
from rating.adapters.lichess import Lichess
from rating.adapters.requests_http import RequestsHttpAdapter
from rating.adapters.sqlite_profile_log import SQLiteProfileLogAdapter
from rating.adapters.uscf import USCF, AmbiguousUSCFPlayerError
from rating.config_loader import ConfigLoader
from rating.domain.models import CANONICAL_RATING_KEYS, NormalizedRatingProfile
from rating.ports.profile_log_port import ProfileLogPort


def _format_rating_value(value) -> str:
    """Render a normalized rating value for plain-text CLI output."""
    return "Not rated" if value is None else str(value)


def _to_json(profile: NormalizedRatingProfile) -> str:
    """Convert a normalized rating profile into formatted JSON."""
    return json.dumps(profile.to_dict(), indent=4)


def _to_pipe(profile: NormalizedRatingProfile, verbose: bool = False) -> str:
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

    if verbose and profile.metadata.source_url is not None:
        parts.append(f"source_url={profile.metadata.source_url}")

    return "\n".join(parts)


def _add_rating_key_options(parser: argparse.ArgumentParser) -> None:
    """Add the mutually exclusive --standard/--rapid/--blitz/--bullet/--correspondence flags."""
    rating_group = parser.add_mutually_exclusive_group()
    rating_group.add_argument(
        "--standard",
        dest="rating_key",
        action="store_const",
        const="standard",
        help="Use the standard rating (default except for Chess.com)",
    )
    rating_group.add_argument(
        "--rapid",
        dest="rating_key",
        action="store_const",
        const="rapid",
        help="Use the rapid rating (default for Chess.com)",
    )
    rating_group.add_argument(
        "--blitz",
        dest="rating_key",
        action="store_const",
        const="blitz",
        help="Use the blitz rating",
    )
    rating_group.add_argument(
        "--bullet",
        dest="rating_key",
        action="store_const",
        const="bullet",
        help="Use the bullet rating",
    )
    rating_group.add_argument(
        "--correspondence",
        dest="rating_key",
        action="store_const",
        const="correspondence",
        help="Use the correspondence rating",
    )


def _build_fetch_parser() -> argparse.ArgumentParser:
    """Create the parser for normal rating-fetch commands."""
    parser = argparse.ArgumentParser(
        prog="rating",
        description=(
            "Fetches and prints a players's chess rating from USCF, FIDE, "
            "Lichess, or Chess.com.\n\n"
            "Special commands:\n"
            "  rating config\n"
            "    Print the active configuration file path and its contents.\n"
            "  rating history [player] -u|-l|-c|-f [--standard|--rapid|--blitz|\n"
            "    --bullet|--correspondence] [-g|-j]\n"
            "    Print a player's logged rating history for one category, or\n"
            "    plot it as a line graph PNG with --graph. Uses the\n"
            "    platform's configured default player if omitted."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("player", nargs="?", default=None, help="The player's ID or name.")
    parser.add_argument("-j", "--json", action="store_true", help="Create JSON output")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Include additional metadata (e.g. source URL) in plain-text output",
    )

    _add_rating_key_options(parser)
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


def _build_history_parser() -> argparse.ArgumentParser:
    """Create the parser for the rating-history report command."""
    parser = argparse.ArgumentParser(
        prog="rating history",
        description="Show a player's rating history over time for one category.",
    )
    parser.add_argument(
        "player",
        nargs="?",
        default=None,
        help="The player's ID as stored in the database (default: the "
        "configured default user for the selected platform).",
    )
    _add_rating_key_options(parser)
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("-j", "--json", action="store_true", help="Create JSON output")
    output_group.add_argument(
        "-g",
        "--graph",
        action="store_true",
        help="Plot the history as a line graph, save it as a PNG image, and "
        "pop it up in a window if a display is available",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output path for --graph (default: <tmpdir>/<provider>_<player>_<category>.png)",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--uscf", action="store_true", help="Use USCF platform")
    group.add_argument("-l", "--lichess", action="store_true", help="Use Lichess platform")
    group.add_argument("-c", "--chess", action="store_true", help="Use chess.com platform")
    group.add_argument("-f", "--fide", action="store_true", help="Use FIDE platform")
    return parser


def _handle_history_command(
    argv: list[str], config: dict, profile_log: Optional[SQLiteProfileLogAdapter] = None
) -> None:
    """Print a player's rating history for one category, then exit."""
    args = _build_history_parser().parse_args(argv)

    if args.lichess:
        provider = "lichess"
        player = args.player or config["lichess"]["defaultUser"]
    elif args.chess:
        provider = "chesscom"
        player = args.player or config["Chess"]["defaultUser"]
    elif args.fide:
        provider = "fide"
        player = args.player or config["FIDE"]["defaultUser"]
    else:
        provider = "uscf"
        player = args.player or config["USCF"]["defaultUser"]

    category = args.rating_key or ("rapid" if args.chess else "standard")

    if profile_log is None:
        profile_log = SQLiteProfileLogAdapter(config["DBFILE"])
    rows = profile_log.history(provider, player, category)

    if not rows:
        print(f'No "{category}" history found for {provider} player "{player}"')
        return

    if args.graph:
        path = _write_graph(rows, provider, player, category, args.output)
        print(f"Wrote {path}")
    elif args.json:
        print(json.dumps([{"as_of": when, "value": value} for when, value in rows], indent=4))
    else:
        for when, value in rows:
            print(f"{when}\t{_format_rating_value(value)}")


def _write_graph(
    rows: list, provider: str, player: str, category: str, output_path: Optional[str]
) -> str:
    """Plot ``rows`` as a line graph and save it as a PNG. Returns the path.

    Also pops up an interactive window when a GUI backend is available
    (matplotlib falls back to the non-interactive Agg backend on its own in
    headless environments like cron, so no window is shown there).
    """
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    dates = [_parse_when(when) for when, _ in rows]
    values = [float("nan") if value is None else value for _, value in rows]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, values, marker="o", linewidth=1.5, markersize=3)
    ax.set_title(f"{provider} {category} rating history for {player}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Rating")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    path = output_path or os.path.join(
        tempfile.gettempdir(), f"{provider}_{player}_{category}.png"
    )
    fig.savefig(path)
    _show_graph(fig)
    return path


def _show_graph(fig) -> None:
    """Display ``fig`` in a window, or just close it under a headless backend."""
    import matplotlib
    import matplotlib.pyplot as plt

    if matplotlib.get_backend().lower() == "agg":
        plt.close(fig)
    else:
        plt.show()


def _parse_when(value: str):
    """Parse a ``history()`` timestamp string into a ``datetime``.

    Rows carry either a bare date (USCF's ``as_of``) or a full logged-at
    timestamp, so both formats must be tried.
    """
    from datetime import datetime

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized timestamp format: {value!r}")


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
    argv = sys.argv[1:]
    if argv and argv[0] == "config":
        loader = ConfigLoader()
        _handle_config_command(argv[1:], loader)
        return

    if argv and argv[0] == "history":
        loader = ConfigLoader()
        _handle_history_command(argv[1:], loader.config)
        return

    args = _build_fetch_parser().parse_args(argv)
    loader = ConfigLoader()
    config = loader.config

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

    try:
        profile = app.fetch()
    except AmbiguousUSCFPlayerError as exc:
        print(f'Multiple USCF members match "{exc.query}":')
        for candidate in exc.candidates:
            print(f'  {candidate["id"]}\t{candidate["name"]}\t{candidate["state"]}')
        print("Rerun with -u <id> using one of the IDs above.")
        return

    if not profile:
        print(f'No ratings found for "{player}"')
    else:
        log_profile(profile, config["DBFILE"])
        if args.json:
            print(_to_json(profile))
        elif args.verbose:
            print(_to_pipe(profile, args.verbose))
        else:
            rating_key = args.rating_key or ("rapid" if args.chess else "standard")
            print(_format_rating_value(profile.ratings[rating_key]))


def log_profile(
    profile: NormalizedRatingProfile,
    database_path: str,
    profile_log: Optional[ProfileLogPort] = None,
) -> None:
    """Record a fetched profile through the configured outbound logging port."""
    if profile_log is None:
        profile_log = SQLiteProfileLogAdapter(database_path)
    profile_log.log(profile)


if __name__ == "__main__":
    main()
