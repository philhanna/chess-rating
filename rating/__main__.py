#! /usr/bin/python
"""Compatibility wrapper for ``python -m rating``.

The real CLI composition root lives in :mod:`rating.application.rating`.
Keeping this module as a thin forwarder preserves the standard package-module
entry point while allowing the application layer to grow additional CLIs.
"""

from rating.application.rating import main


if __name__ == "__main__":
    main()
