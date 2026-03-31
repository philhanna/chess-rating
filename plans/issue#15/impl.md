Issue `#15` is now implemented as persistent logging controls for database-backed rating history.

The main CLI in [rating.py](/home/saspeh/dev/python/chess-rating/rating/application/rating.py) now supports a dedicated `logging` command alongside the existing fetch flow:

- `rating logging`
- `rating logging status`
- `rating logging on`
- `rating logging off`

These commands behave like `--help` or `--version`: they perform the requested config action, print the current logging state, and then exit without running a normal rating lookup. The existing fetch path remains available as bare `rating ...`, and it now persists history only when `database.enabled` is `true` and `--dry-run` was not passed.

Configuration support was extended in [config_loader.py](/home/saspeh/dev/python/chess-rating/rating/config_loader.py). The loader now ensures there is always a `database.enabled` entry, defaulting to `True` so existing config files preserve the previous behavior of saving successful fetches. The same loader also now provides `set_database_enabled()`, which updates `config.yaml` while preserving comments and unrelated formatting.

Because preserving comments in `config.yaml` was a hard requirement, the implementation added `ruamel.yaml` in [pyproject.toml](/home/saspeh/dev/python/chess-rating/pyproject.toml) and uses its round-trip YAML support for writes. That lets `rating logging on|off` change only `database.enabled` without stripping section comments, inline comments, or other settings.

The sample configuration in [sample_config.yaml](/home/saspeh/dev/python/chess-rating/sample_config.yaml) now documents the new setting:

- `database.path`
- `database.enabled`

Test coverage was expanded in two places. [test_config_loader.py](/home/saspeh/dev/python/chess-rating/tests/test_config_loader.py) now verifies the default value for `database.enabled` and checks that toggling the setting preserves comments. [test_rating_application.py](/home/saspeh/dev/python/chess-rating/tests/test_rating_application.py) now verifies the `logging` command behavior, confirms that disabled logging suppresses persistence, and confirms that `--dry-run` still overrides persistence for a single invocation.

Verification passed with the full default test suite using the project virtual environment after installing `ruamel.yaml`:

```bash
python -m pytest
```

The result was `82 passed, 7 deselected`.
