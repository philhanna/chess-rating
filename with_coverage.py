"""Run the test suite with coverage using the current interpreter.

This helper avoids shell-specific activation and path logic so it works on
Windows, macOS, and Linux.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    command = [sys.executable, "-m", "pytest", "-v", "--cov=rating"]
    completed = subprocess.run(command, cwd=script_dir)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

