# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
