# Chess Rating Overview

## Project Overview
CLI tool that fetches and prints a player's chess rating from USCF, FIDE, Lichess, or Chess.com.

Run: `rating [-u|-l|-c|-f] [player]`

## Architecture
Hexagonal (ports and adapters):

- `rating/ports/rating_port.py` — abstract `RatingPort` (each platform implements `fetch() -> str`)
- `rating/ports/http_port.py` — abstract `HttpPort` (infrastructure adapter for HTTP)
- `rating/adapters/` — one file per platform (`uscf.py`, `lichess.py`, `chesscom.py`, `fide.py`) plus `requests_http.py` (the real HTTP adapter)
- `rating/__main__.py` — CLI entry point; wires up adapters via argparse
- `rating/config_loader.py` — loads `sample_config.yaml` for default usernames per platform

## Documentation
- `docs/overview.md` — high-level project notes and test workflow
- `docs/system_tests.md` — notes on system-test markers and how to run them
- `docs/uscf_functions.md` — call tree for the legacy USCF helper port in `tests/uscf_functions.py`

## Running Tests
```bash
pytest                  # unit tests only (system tests excluded by default)
./with_coverage.sh      # pytest -v --cov=rating
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
- `tests/uscf_functions.py` is a Python port of the legacy US Chess helper logic used by the tests

## Dependencies
- Runtime: `requests`, `beautifulsoup4`, `numpy`, `platformdirs`, `PyYAML`
- Dev/test extra: `pytest`, `pytest-cov`, `coverage`
- Install runtime package: `pip install .`
- Install with dev tools: `pip install .[dev]`
- Virtual environment: `venv/`
