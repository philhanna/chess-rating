# System Tests

System tests live in `tests/test_live.py` and are marked `@pytest.mark.system`. They invoke `python -m rating` as a subprocess and make real network calls, so they are excluded from the default test run.

## Running tests

```bash
pytest                  # unit tests only (system tests excluded by default)
pytest -m system        # system tests only
pytest -m ""            # all tests, including system tests
```

The exclusion is enforced by `addopts = '-m "not system"'` in `[tool.pytest.ini_options]` in `pyproject.toml`.

## What the system tests cover

Each test in `test_live.py` runs the CLI as a subprocess and checks the return code and output:

| Test | Command |
|---|---|
| `test_help_option` | `python -m rating --help` |
| `test_uscf_option` | `python -m rating someplayer --uscf` |
| `test_lichess_option` | `python -m rating someplayer --lichess` |
| `test_chesscom_option` | `python -m rating someplayer --chess` |
| `test_fide_option` | `python -m rating 1503014 --fide` |
| `test_default_uscf` | `python -m rating someplayer` (defaults to USCF) |
| `test_invalid_option` | `python -m rating someplayer --invalid` (expects non-zero exit) |

## Adding a new system test

Mark it with `@pytest.mark.system` and use `subprocess.run` to invoke the CLI:

```python
@pytest.mark.system
def test_new_platform():
    result = subprocess.run(
        ['python', '-m', 'rating', 'someuser', '--platform'],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
```
