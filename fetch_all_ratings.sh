#! /bin/bash
# Fetch and log this user's rating from every supported provider.
#
# Each call logs a new snapshot to the SQLite database configured by
# DBFILE in the active .env file (see `rating config`), using that
# platform's configured default player. Intended to run nightly via cron.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RATING_BIN="${SCRIPT_DIR}/.venv/bin/rating"

if [ ! -x "${RATING_BIN}" ]; then
    RATING_BIN="rating"
fi

status=0
for flag in -u -l -c -f; do
    "${RATING_BIN}" "${flag}" -v || status=1
done

exit "${status}"
