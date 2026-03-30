#! /bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python"

if [ ! -x "${PYTHON_BIN}" ]; then
    PYTHON_BIN="python"
fi

"${PYTHON_BIN}" -m pytest -v --cov=rating
