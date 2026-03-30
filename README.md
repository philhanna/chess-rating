# Chess rating

A Python command-line tool that retrieves and prints the chess rating of a person from the specified ratings platform.

## Setup

Install the package and its runtime dependencies with:

```bash
python -m pip install -e .
```

If you also want the development and test tools, install the optional `dev` extra:

```bash
python -m pip install -e '.[dev]'
```

After installation, the CLI is available as:

```bash
rating --help
```

## Running tests

Run the default test suite with:

```bash
pytest
```

System tests are marked with `@pytest.mark.system` and excluded by default. Run them explicitly with:

```bash
pytest -m system
```

## Running the CLI

Use the installed console script:

```bash
rating -u some_uscf_id
rating -l some_lichess_user
rating -c some_chesscom_user
rating -f some_fide_id
```

You can still run the module directly with `python -m rating`, but the packaged command is the preferred entry point.

## How to call
```
usage: rating [-h] [-v] [-j] [-u | -l | -c | -f] [player]

Fetches and prints a players's chess rating from USCF, FIDE, Lichess, or Chess.com.

positional arguments:
  player         The player's ID or name.

options:
  -h, --help     show this help message and exit
  -v, --version  show the project version and exit
  -j, --json     Create JSON output
  -u, --uscf     Use USCF platform
  -l, --lichess  Use Lichess platform
  -c, --chess    Use chess.com platform
  -f, --fide     Use FIDE platform
```

## Chess.com
Data from chess.com is obtained using this URL:

https://api.chess.com/pub/player/{userid}/stats

A get request for that URL returns JSON that looks like this:
```json
{
  "chess_daily": {
    "last": {
      "rating": 1018,
      "date": 1741387755,
      "rd": 82
    },
    "best": {
      "rating": 1200,
      "date": 1715625334,
      "game": "https://www.chess.com/game/daily/708913025"
    },
    "record": {
      "win": 19,
      "loss": 15,
      "draw": 1,
      "time_per_move": 9703,
      "timeout_percent": 0
    }
  },
  "chess_rapid": {
    "last": {
      "rating": 970,
      "date": 1740903985,
      "rd": 43
    },
    "best": {
      "rating": 1108,
      "date": 1733977950,
      "game": "https://www.chess.com/game/live/109817472659"
    },
    "record": {
      "win": 458,
      "loss": 432,
      "draw": 41
    }
  },
  ...
}
