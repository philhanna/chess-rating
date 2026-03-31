Today, successful rating fetches are written to the history database by default, and `--dry-run` disables that behavior for a single invocation. We want to keep the one-time override behavior of `--dry-run`, but add a persistent way to turn database logging on or off and to inspect its current state.

## Proposed CLI behavior

Add a `logging` command with three actions:

- `rating logging on`
- `rating logging off`
- `rating logging status`

This command should behave like `--help` or `--version`: it performs the requested action, prints an appropriate message, and then exits without running the normal rating-fetch flow.

### Expected semantics

- `rating logging on`
  Persistently enable database logging by updating `config.yaml`.
- `rating logging off`
  Persistently disable database logging by updating `config.yaml`.
- `rating logging status`
  Report whether database logging is currently enabled or disabled. This is also the behavior when `on|off|status` is omitted.

## Config changes

Store the persistent setting in the existing config under:

```yaml
database:
  enabled: true
```

The config key should remain `database.enabled` even though the user-facing command is named `logging`. "Logging" is clearer as CLI language, while `database.enabled` is the more precise persistent setting.

If the key is missing, the loader should provide a sensible default so existing configs continue to work.

## Interaction with `--dry-run`

Keep `--dry-run`, but narrow its meaning to a one-time runtime override:

- If logging is enabled in config, `--dry-run` skips persistence for that invocation only.
- If logging is disabled in config, normal runs do not persist.
- `rating logging on|off|status` is a config-management command and should not be combined with the normal fetch path.

In other words:

- `logging` manages the persistent default
- `--dry-run` overrides persistence once for the current fetch

## Why this design

- It cleanly separates configuration management from normal rating lookup.
- It avoids overloading flags with persistent side effects.
- It keeps `--dry-run` aligned with common CLI expectations: do the usual work, but skip the side effect for this run.
- It gives users an explicit, discoverable command for checking and changing the long-term logging state.

## Suggested implementation shape

- Add support for a `logging` command in the CLI.
- Update the config loader to read and default `database.enabled`.
- Add a way to write updated config values back to `config.yaml` without changing any other settings or comments.
- Ensure the normal fetch flow consults `database.enabled` before saving history.
- Ensure `--dry-run` still bypasses persistence for a single run.

## Acceptance criteria

- `rating logging on` updates `config.yaml` so `database.enabled` is `true`, prints confirmation, and exits.
- `rating logging off` updates `config.yaml` so `database.enabled` is `false`, prints confirmation, and exits.
- `rating logging status` or `rating logging` prints the current persisted logging status and exits.
- Normal rating fetches persist only when `database.enabled` is `true`.
- `--dry-run` prevents persistence for the current invocation only.
- Existing configs without `database.enabled` continue to work via a default value.
