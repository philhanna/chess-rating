# Chess rating

A Python command-line tool that retrieves and prints the chess rating of a person from the specified ratings platform.

## Setup

Clone this repository and change directory into its root,
then create a Python virtual environment in which to run it:

```bash
git clone git@github.com:philhanna/chess-rating.git
cd chess-rating
python -m venv .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

On Windows PowerShell use:

```powershell
.venv\Scripts\Activate.ps1
```

Copy the sample environment file `sample.env` into the configuration
directory for your platform as `.env`:

- Linux: `~/.config/chess-rating/.env`
- macOS: `~/Library/Application Support/chess-rating/.env`
- Windows: `%APPDATA%\chess-rating\.env`

The file uses standard dotenv syntax:

```dotenv
LICHESS_DEFAULT_USER=pehanna
USCF_DEFAULT_USER=12910923
CHESS_DEFAULT_USER=pehanna7
FIDE_DEFAULT_USER=30976537
```

Install the package and its runtime dependencies with:

```bash
python -m pip install -e .
```
_note the "." after the -e option!_

After installation, the CLI is available as:

```bash
rating --help
```

On Windows, if your shell has not refreshed its `PATH` yet, you can also run:

```powershell
.venv\Scripts\rating.exe --help
```

## Running with Docker

The container runs on Linux and on Windows with Docker Desktop using Linux
containers. The Compose configuration mounts the host configuration file into
the container as read-only; it never copies the file into the image.

On Linux, the default host path is `~/.config/chess-rating/.env`, so you can
build and run directly:

```bash
docker compose build
docker compose run --rm rating -u
docker compose run --rm rating -l --rapid some_lichess_user
docker compose run --rm rating config
```

On Windows PowerShell, select the host configuration file before running the
same Compose commands. Use the first path if you keep the file under `.config`,
or the second for the normal Windows application-data location:

```powershell
$env:CHESS_RATING_CONFIG_FILE = "$HOME\.config\chess-rating\.env"
# Or: $env:CHESS_RATING_CONFIG_FILE = "$env:APPDATA\chess-rating\.env"

docker compose build
docker compose run --rm rating -u
docker compose run --rm rating -l --rapid some_lichess_user
docker compose run --rm rating config
```

`CHESS_RATING_CONFIG_FILE` can also point to another absolute host path on
either operating system. The variable only controls the bind-mount source; the
container always sees the file at its Linux configuration path.

Running the service without arguments displays the CLI help:

```bash
docker compose run --rm rating
```

Make sure the selected configuration file exists before starting the
container. If `CHESS_RATING_CONFIG_FILE` is unset, Compose uses
`${HOME}/.config/chess-rating/.env`.

To run the image without Compose, build it and bind-mount the same file:

```bash
docker build -t chess-rating .
docker run --rm \
  --mount type=bind,src="${HOME}/.config/chess-rating/.env",dst=/home/rating/.config/chess-rating/.env,readonly \
  chess-rating -u
```

The equivalent direct Docker command in Windows PowerShell is:

```powershell
docker build -t chess-rating .
docker run --rm `
  --mount "type=bind,src=$env:CHESS_RATING_CONFIG_FILE,dst=/home/rating/.config/chess-rating/.env,readonly" `
  chess-rating -u
```

## Running the CLI

Use the installed console script:

```bash
rating -u some_uscf_id
rating -l --rapid some_lichess_user
rating -c some_chesscom_user
rating -f some_fide_id
```

Choose the rating to print with `--standard`, `--rapid`, `--blitz`,
`--bullet`, or `--correspondence`. The options are mutually exclusive, and
`--standard` is used when none is supplied except for Chess.com, which defaults
to `--rapid`. If the selected rating is not available for the player or
platform, the command prints `Not rated`.

The rating selector applies to the normal single-value output. `--json` and
`--verbose` continue to display the full normalized profile.

You can still run the module directly with `python -m rating`, but the packaged command is the preferred entry point. The main CLI implementation lives in `rating.application.rating`, while `rating.__main__` remains a thin compatibility wrapper.

## How to call
```
usage: rating [-h] [-j] [-v]
              [--standard | --rapid | --blitz | --bullet | --correspondence]
              (-u | -l | -c | -f)
              [player]

Fetches and prints a players's chess rating from USCF, FIDE, Lichess, or Chess.com.

Special commands:
  rating config
    Print the active configuration file path and its contents.

positional arguments:
  player            The player's ID or name.

options:
  -h, --help        show this help message and exit
  -j, --json        Create JSON output
  -v, --verbose     Include additional metadata (e.g. source URL) in plain-
                    text output
  --standard        Use the standard rating (default except for Chess.com)
  --rapid           Use the rapid rating (default for Chess.com)
  --blitz           Use the blitz rating
  --bullet          Use the bullet rating
  --correspondence  Use the correspondence rating
  -u, --uscf        Use USCF platform
  -l, --lichess     Use Lichess platform
  -c, --chess       Use chess.com platform
  -f, --fide        Use FIDE platform
```

One source flag is required for rating lookups. For example, use `rating --uscf 12910923`
rather than relying on an implicit default source.

Run `rating config` to print the active configuration file's path and its
contents.

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
```

The application reads the `chess_*` categories from this response and
normalizes them into the shared rating profile schema. For example:

- `chess_rapid.last.rating` -> `ratings.rapid`
- `chess_blitz.last.rating` -> `ratings.blitz`
- `chess_bullet.last.rating` -> `ratings.bullet`
- `chess_daily.last.rating` -> `ratings.correspondence`

## Lichess
Data from Lichess is obtained using this URL:

https://lichess.org/api/user/{userid}

A get request for that URL returns JSON that includes a `perfs` object like
this:

```json
{
  "id": "pehanna",
  "username": "pehanna",
  "perfs": {
    "bullet": {
      "games": 5,
      "rating": 1500
    },
    "blitz": {
      "games": 10,
      "rating": 1600
    },
    "rapid": {
      "games": 0,
      "rating": 1400
    },
    "classical": {
      "games": 7,
      "rating": 1700
    },
    "puzzle": {
      "games": 3,
      "rating": 2100
    }
  }
}
```

The application keeps only categories with at least one game played and
normalizes them like this:

- `classical` -> `ratings.standard`
- `rapid` -> `ratings.rapid`
- `blitz` -> `ratings.blitz`
- `bullet` -> `ratings.bullet`
- provider-specific categories such as `puzzle` or `ultraBullet` -> `extras`

## USCF
Data from US Chess is obtained using this URL:

https://ratings-api.uschess.org/api/v1/members/{userid}/sections

A get request for that URL returns JSON containing a list of section results
for the player, such as:

```json
{
  "items": [
    {
      "sectionNumber": 1,
      "sectionName": "March U1600",
      "startDate": "2026-03-04",
      "endDate": "2026-03-25",
      "ratingSystem": "R",
      "ratingRecords": [
        {
          "preRating": 1227,
          "postRating": 1260,
          "ratingSource": "R"
        }
      ],
      "event": {
        "id": "202603250203",
        "name": "Triangle Chess Adults Marathon March",
        "stateCode": "NC"
      }
    }
  ]
}
```

The application currently uses the newest section entry only. From that first
item, it extracts:

- `items[0].ratingRecords[0].postRating` -> `ratings.standard`
- `items[0].endDate` -> `metadata.as_of`

For more detail on this payload shape, see
[docs/uscf_sections.md](/home/saspeh/dev/python/chess-rating/docs/uscf_sections.md).

## FIDE
Data from FIDE is obtained using this URL:

https://ratings.fide.com/profile/{userid}

FIDE does not provide the needed data as a simple JSON API for this use case,
so the application reads the public HTML profile page and extracts the visible
rating cards. The relevant part of the page looks roughly like this:

```html
<div class="profile-container">
  <h1 class="player-title">Magnus Carlsen</h1>
</div>
<div class="profile-section">
  <div class="profile-games">
    <div>
      <p>2835</p>
      <p>Standard</p>
    </div>
    <div>
      <p>2810</p>
      <p>Rapid</p>
    </div>
    <div>
      <p>2885</p>
      <p>Blitz</p>
    </div>
  </div>
</div>
```

The application scrapes the player name and rating categories from this HTML
and normalizes them like this:

- `Standard` -> `ratings.standard`
- `Rapid` -> `ratings.rapid`
- `Blitz` -> `ratings.blitz`
- values such as `Not rated` -> `null` in JSON output / `Not rated` in plain text
- any additional FIDE categories -> `extras`
