I’d handle issue `#13` as a small persistence feature layered onto the existing ports/adapters structure, not as a rewrite.

The cleanest shape is to add a new persistence port plus an SQLite adapter, then call it from the composition root in [rating/application/rating.py](/home/saspeh/dev/python/chess-rating/rating/application/rating.py). Right now `main()` already has the exact moment we want: fetch the normalized profile, print it, and only then persist if the fetch succeeded. That keeps the provider adapters focused on scraping/parsing and keeps storage as a separate concern.

My implementation plan would be:

1. Add a storage port, something like `HistoryPort.save(profile: NormalizedRatingProfile) -> None`, under `rating/ports/`.
2. Add an SQLite adapter under `rating/adapters/`, responsible for:
   - opening/creating the DB
   - creating schema on first run
   - inserting one row per successful invocation
3. Extend config loading in [rating/config_loader.py](/home/saspeh/dev/python/chess-rating/rating/config_loader.py) with a database path, probably defaulting to a per-user app data location if not set explicitly.
4. Add a `--dry-run` CLI flag in [rating/application/rating.py](/home/saspeh/dev/python/chess-rating/rating/application/rating.py) rather than `--test`. `--test` is a little ambiguous in a CLI because it sounds like a diagnostics mode, while `--dry-run` more clearly communicates “fetch normally, don’t persist”.
5. After `profile = app.fetch()`, persist only when:
   - `profile` is not `None`
   - the run did not raise an error
   - the user did not pass `--dry-run`
6. Add focused tests for:
   - schema creation
   - successful insert
   - no insert on `None`
   - no insert with `--dry-run`
   - provider-specific rows are stored and queryable via the `provider` column

For the schema, I would use a single `rating_history` table with a `provider` column. That keeps the schema simpler, avoids repeating the same structure four times, and still makes provider-specific analysis straightforward. The table would have these columns:
- `id`
- `recorded_at`
- `player_id`
- `display_name`
- canonical ratings: `standard`, `rapid`, `blitz`, `bullet`, `correspondence`
- `extras_json`
- `as_of`
- `source_url`

The important design choice is storing provider-specific extras as JSON rather than endlessly widening the schema. That fits the existing normalized model in [rating/domain/models.py](/home/saspeh/dev/python/chess-rating/rating/domain/models.py): canonical fields stay queryable as columns, while `extras` remains flexible.

If we wanted to keep it especially tidy, I’d also extract the current `main()` orchestration a bit so the flow becomes “parse args -> fetch profile -> render output -> optionally persist”. That will make the new behavior easier to test than bolting SQLite calls directly into the middle of the current function.

We have now agreed to reinterpret that part of the issue and standardize on one `rating_history` table with a `provider` column, which is the design I would implement.
