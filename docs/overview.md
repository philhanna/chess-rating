# Chess Rating Overview

## Project Overview
CLI tool that fetches and prints a player's chess rating from USCF, FIDE, Lichess, or Chess.com.

Run: `rating [-u|-l|-c|-f] [player] [-j|-v]`

By default the CLI prints just the player's primary rating value. Pass `-v`
for verbose pipe-delimited output (all ratings plus metadata) or `-j` for
JSON. For USCF (`-u`), `player` may be a numeric member ID or a name; a name
is resolved via fuzzy search, and multiple matches raise
`AmbiguousUSCFPlayerError`, printing the candidate list instead of a rating.

`rating config` prints the active configuration file path and its contents.

## Architecture
Hexagonal (ports and adapters):

- `rating/ports/rating_port.py` — abstract `RatingPort` (each platform implements `fetch() -> NormalizedRatingProfile | None` and `getPrimaryRatingKey() -> str`)
- `rating/ports/http_port.py` — abstract `HttpPort` (infrastructure adapter for HTTP)
- `rating/adapters/` — one file per platform (`uscf.py`, `lichess.py`, `chesscom.py`, `fide.py`) plus `requests_http.py` (the real HTTP adapter); `uscf.py` also resolves player names to member IDs and defines `AmbiguousUSCFPlayerError`
- `rating/domain/models.py` — provider-independent domain models (`NormalizedRatingProfile`, `PlayerIdentity`, `RatingMetadata`) and helpers (`build_ratings`, `normalize_rating_value`, `to_snake_case`)
- `rating/application/rating.py` — CLI composition root; wires up adapters via argparse
- `rating/__main__.py` — thin wrapper that preserves `python -m rating`
- `rating/config_loader.py` — loads the user's `.env` file from the platform-specific config directory, with `sample.env` as the example template

See `docs/ports_and_adapters.md` for the full dependency picture.

## Documentation
- `docs/overview.md` — high-level project notes and test workflow
- `docs/ports_and_adapters.md` — where the composition root lives and how ports are wired to adapters
- `docs/system_tests.md` — notes on system-test markers and how to run them
- `docs/uscf_sections.md` — inferred schema of the USCF sections API payload used in tests

## Running Tests
```bash
pytest                  # unit tests only (system tests excluded by default)
python with_coverage.py # cross-platform coverage helper
```

On Unix-like systems, `./with_coverage.sh` remains available as a thin wrapper.

Coverage requires the dev/test dependencies to be installed first:
```bash
python -m pip install -e '.[dev]'
```

System tests (hit real network) are marked `@pytest.mark.system` and excluded by default via the pytest settings in `pyproject.toml`. Run them with:
```bash
pytest -m system
```

The pytest defaults live in `[tool.pytest.ini_options]` in `pyproject.toml`.

## Test Patterns
- Tests mock `HttpPort` using `unittest.mock.Mock(spec=HttpPort)`
- Test data lives in `tests/testdata/` organized by platform
- Each adapter test file: `tests/test_<platform>.py`
- `tests/test_base.py` — shared port contract tests (abstract port instantiation, `fetch()` chain)
- `tests/test_http_get.py` — unit tests for `RequestsHttpAdapter` (success, HTTP error, network error, timeout)
- `tests/test_config_loader.py` — unit tests for `config_loader`
- `tests/test_rating_application.py` — unit tests for the CLI composition root
- `tests/test_live.py` — system tests (marked `@pytest.mark.system`) that invoke the current Python interpreter as a subprocess
- `tests/test_uscf.py` — covers USCF name-to-member-ID resolution and the `AmbiguousUSCFPlayerError` multi-match path, not exercised by system tests
- `tests/uscf_functions.py` is a Python port of the legacy US Chess helper logic used by the tests

## Dependencies
- Runtime: `requests`, `beautifulsoup4`, `numpy`, `platformdirs`, `python-dotenv`
- Dev/test extra: `pytest`, `pytest-cov`, `coverage`
- Install runtime package: `pip install .`
- Install with dev tools: `pip install .[dev]`
- Virtual environment: `.venv/`
