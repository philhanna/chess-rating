Issue `#13` is now implemented as SQLite-backed history persistence for successful CLI runs.

The main CLI in [rating.py](/home/saspeh/dev/python/chess-rating/rating/application/rating.py) now accepts `--dry-run`, which preserves the existing fetch-and-print behavior while skipping persistence. On normal successful runs, the CLI saves the returned `NormalizedRatingProfile` after `fetch()` succeeds and before rendering output. Runs that return `None` still print the existing not-found message and do not write to the database.

Persistence was added through the existing ports/adapters structure instead of embedding SQLite logic directly in the CLI. A new abstract persistence boundary lives in [history_port.py](/home/saspeh/dev/python/chess-rating/rating/ports/history_port.py), and the concrete SQLite implementation lives in [sqlite_history.py](/home/saspeh/dev/python/chess-rating/rating/adapters/sqlite_history.py). The adapter creates the schema on demand and stores snapshots in a single `rating_history` table with these fields:

- `id`
- `recorded_at`
- `provider`
- `player_id`
- `display_name`
- `standard`
- `rapid`
- `blitz`
- `bullet`
- `correspondence`
- `extras_json`
- `as_of`
- `source_url`

This follows the revised design decision to use one table with a `provider` column rather than one table per source. Provider-specific extra ratings are serialized into `extras_json`, while the canonical rating categories remain first-class columns for straightforward querying later.

Configuration support was extended in [config_loader.py](/home/saspeh/dev/python/chess-rating/rating/config_loader.py). The loader now ensures there is always a `database.path` entry, defaulting to a per-user data directory when the config file does not specify one explicitly. The sample configuration in [sample_config.yaml](/home/saspeh/dev/python/chess-rating/sample_config.yaml) now includes a `database` section as an example.

Test coverage was added in two places. [test_rating_application.py](/home/saspeh/dev/python/chess-rating/tests/test_rating_application.py) verifies that successful CLI runs save history, missing profiles do not, and `--dry-run` suppresses persistence. [test_sqlite_history.py](/home/saspeh/dev/python/chess-rating/tests/test_sqlite_history.py) verifies schema creation and inserts into the shared history table. The full default test suite passed after the change with `python -m pytest`.
