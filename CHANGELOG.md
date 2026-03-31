# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]
- Added `rating logging [on|off|status]` to inspect or change persistent history logging from the CLI.
- Added `rating config` to print the active configuration file path and its contents.
- Require an explicit source flag (`--uscf`, `--lichess`, `--chess`, or `--fide`) for rating lookups instead of defaulting to USCF.
- Changed plain-text output from pipe-delimited fields to newline-separated `key=value` lines and omitted unrated canonical categories.
- Added a persistent `database.enabled` configuration setting with defaults in the sample config and support for preserving YAML comments when toggling it.
- Hardened the USCF adapter so incomplete or missing section data returns no profile instead of raising parsing errors.
- Expanded tests and README documentation for the new CLI commands, configuration behavior, and output format.

## [1.4.0] - 2026-03-30
- Added SQLite-backed rating history persistence using a single `rating_history` table with a `provider` column.
- Added a persistence port and SQLite adapter so successful CLI runs are recorded without coupling storage logic to the provider adapters.
- Added the `--dry-run` CLI option to fetch and print ratings without writing to the history database.
- Extended configuration loading with a default per-user database path and documented the database setting in `sample_config.yaml`.
- Added tests covering CLI persistence behavior and SQLite history storage.
- Simplified the CLI help test to avoid the `runpy` warning during pytest runs.

## [1.3.0] - 2026-03-29
- Normalized all four rating-source adapters to return a shared domain schema with canonical rating categories, provider metadata, and provider-specific extras.
- Added the new `rating.domain` package to hold normalized rating models and helper functions.
- Updated the CLI to render both plain text and JSON from normalized rating profiles instead of provider-specific pipe strings.
- Revised adapter tests to validate the normalized schema across USCF, FIDE, Lichess, and Chess.com.

## [1.2.0] - 2026-03-29

- Added the packaged `rating` CLI entry point with `--version` and JSON output support.
- Organized project documentation under `docs/`, including architecture and USCF helper references.
- Moved pytest and dependency configuration into `pyproject.toml`.
- Added `CHANGELOG.md` and the MIT `LICENSE`.
- Improved internal documentation in the CLI and configuration loader modules.

## [0.1.0] - Initial release

- Initial CLI support for fetching chess ratings from USCF, FIDE, Lichess, and Chess.com.
- Hexagonal project structure with platform adapters and HTTP abstraction.
- Automated tests for adapters and configuration loading.
