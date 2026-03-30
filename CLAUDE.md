# Chess Rating — Claude Code Notes

## Project Overview
CLI tool that fetches and prints a player's chess rating from USCF, FIDE, Lichess, or Chess.com.

Run: `python -m rating [-u|-l|-c|-f] [player]`

## Architecture
Hexagonal (ports and adapters):

- `rating/ports/rating_port.py` — abstract `RatingPort` (each platform implements `fetch() -> str`)
- `rating/ports/http_port.py` — abstract `HttpPort` (infrastructure adapter for HTTP)
- `rating/adapters/` — one file per platform (`uscf.py`, `lichess.py`, `chesscom.py`, `fide.py`) plus `requests_http.py` (the real HTTP adapter)
- `rating/__main__.py` — CLI entry point; wires up adapters via argparse
- `rating/config_loader.py` — loads `sample_config.yaml` for default usernames per platform

## Running Tests
```bash
pytest                  # unit tests only (system tests excluded by default)
./with_coverage.sh      # pytest -v --cov=rating
```

System tests (hit real network) are marked `@pytest.mark.system` and excluded by default via the pytest settings in `pyproject.toml`. Run them with:
```bash
pytest -m system
```

## Test Patterns
- Tests mock `HttpPort` using `unittest.mock.Mock(spec=HttpPort)`
- Test data (HTML/JSON fixtures) lives in `testdata/` organized by platform
- Each adapter test file: `tests/test_<platform>.py`

## Dependencies
- `requests`, `bs4` (BeautifulSoup), `numpy`
- Install: `pip install -r requirements.txt`
- Virtual environment: `venv/`
