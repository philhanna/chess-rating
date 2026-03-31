I’d implement issue `#15` as a small CLI-and-config enhancement layered onto the existing composition root, not as a broad rewrite of the command-line interface.

The current structure in [rating/application/rating.py](/home/saspeh/dev/python/chess-rating/rating/application/rating.py) already has one clear responsibility: parse the normal fetch arguments, build the selected adapter, fetch a profile, render it, and optionally persist it. The new `logging` behavior is different in kind because it is a config-management command that should behave like `--help` or `--version`: do one thing, print a result, and exit.

Because the fetch flow still needs to work as bare `rating ...` without introducing a mandatory subcommand, the cleanest implementation is to dispatch early:

1. If the first positional token is `logging`, handle the logging command and exit.
2. Otherwise, continue through the existing fetch parser and fetch flow.

That approach keeps the normal CLI stable and avoids forcing the whole application into an argparse subparser redesign just to support one config command.

My implementation plan would be:

1. Extend [rating/config_loader.py](/home/saspeh/dev/python/chess-rating/rating/config_loader.py) so the loaded config always includes:
   - `database.path`
   - `database.enabled`
2. Add write support to `ConfigLoader` so it can update `database.enabled` in `config.yaml`.
3. Add a dedicated logging-command parser in [rating/application/rating.py](/home/saspeh/dev/python/chess-rating/rating/application/rating.py) for:
   - `rating logging`
   - `rating logging on`
   - `rating logging off`
   - `rating logging status`
4. Make `rating logging` default to `status`, then print the current state and exit.
5. Change the normal fetch flow so persistence only happens when:
   - a profile was successfully fetched
   - `database.enabled` is `true`
   - `--dry-run` was not passed
6. Add focused tests for both the new logging command and the updated persistence rules.

For the CLI itself, I would not merge logging management into the existing fetch parser. Instead, I’d add a small helper that looks at the raw argv before normal parsing. In pseudocode, the top-level flow becomes:

```python
argv = sys.argv[1:]
if argv and argv[0] == "logging":
    handle_logging_command(argv[1:])
    return

args = parse_fetch_args(argv)
run_fetch_flow(args)
```

That keeps the responsibilities separate:

- `handle_logging_command(...)` manages persistent config and exits
- `run_fetch_flow(...)` performs rating lookup and optional persistence

For the `logging` command parser, I’d use a single optional positional action with `choices=("on", "off", "status")` and `default="status"`. That directly supports the issue requirement that `rating logging` and `rating logging status` behave the same way.

The output behavior should be simple and explicit:

- `rating logging on` prints confirmation that logging is enabled
- `rating logging off` prints confirmation that logging is disabled
- `rating logging status` prints whether logging is currently enabled or disabled

I would keep the persisted config key as `database.enabled`, even though the user-facing command is named `logging`. That keeps the config precise without exposing internal storage language in the CLI.

The most important implementation detail is config writing. The current loader uses PyYAML via `yaml.safe_load()`, which is fine for reading defaults but does not preserve comments or original formatting when writing. Since preserving comments in `config.yaml` is a hard requirement, the implementation must use a round-trip YAML library for writes, most likely `ruamel.yaml`.

Concretely, I’d handle config persistence like this:

1. Keep the current read path responsible for loading config values and supplying defaults.
2. Add a write/update path in `ConfigLoader`, something like:
   - `get_database_enabled() -> bool`
   - `set_database_enabled(enabled: bool) -> None`
3. Implement `set_database_enabled()` with round-trip YAML loading and dumping so only `database.enabled` changes while comments, ordering, and unrelated settings are preserved.

If we want to minimize moving parts, we could switch `ConfigLoader` fully from PyYAML to `ruamel.yaml` for both reading and writing. That would remove the split-brain risk of using one YAML library to read and another to write. Either way, I would not try to hand-edit the file with string replacements; YAML structure and comments are exactly the kind of thing a round-trip parser is for. A plain `yaml.safe_dump()` rewrite would not meet the requirement.

For default behavior, `ConfigLoader` should ensure:

- `config["database"]` exists
- `config["database"]["path"]` defaults to the current per-user database path
- `config["database"]["enabled"]` defaults to `True`

Defaulting `database.enabled` to `True` preserves the current application behavior for existing users and existing config files.

In the fetch path, the persistence rule should become:

```python
database_enabled = config["database"]["enabled"]
should_persist = database_enabled and not args.dry_run
```

Then save only when `should_persist` is true and `profile` is not `None`.

I would also take this opportunity to extract a couple of small helpers from `main()` so the code becomes easier to test:

- one helper to detect and handle `logging`
- one helper to parse normal fetch args
- one helper to decide whether persistence is enabled for the current run

That is enough structure to keep the control flow readable without overengineering the module.

Test coverage should be added in two places.

In [tests/test_config_loader.py](/home/saspeh/dev/python/chess-rating/tests/test_config_loader.py):

- verify `database.enabled` defaults to `True` when omitted
- verify `set_database_enabled(True)` writes `true`
- verify `set_database_enabled(False)` writes `false`
- verify comments and unrelated config entries survive the update
- verify the update changes only the intended setting and does not strip inline or section comments

In [tests/test_rating_application.py](/home/saspeh/dev/python/chess-rating/tests/test_rating_application.py):

- `rating logging` prints status and exits
- `rating logging status` prints status and exits
- `rating logging on` updates config and exits
- `rating logging off` updates config and exits
- normal fetches persist when config says logging is enabled
- normal fetches skip persistence when config says logging is disabled
- `--dry-run` still skips persistence even when logging is enabled

I would also update [sample_config.yaml](/home/saspeh/dev/python/chess-rating/sample_config.yaml) to document the new setting:

```yaml
database:
  path: /tmp/chess-rating.db
  enabled: true
```

The overall shape stays consistent with the current design:

- provider adapters still only fetch and normalize ratings
- SQLite persistence still lives behind the history adapter
- the composition root still decides whether persistence should happen
- config loading remains centralized in `ConfigLoader`

That gives us the requested UX without changing the core architecture of the project.
