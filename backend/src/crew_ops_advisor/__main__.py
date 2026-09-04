"""`python -m crew_ops_advisor` / `crew-ops` entry point. See interface/cli.py."""

from __future__ import annotations

import sys

from crew_ops_advisor.interface.cli import EXIT_ERROR, EXIT_LEGAL, EXIT_NOT_LEGAL, EXIT_OK, main

__all__ = ["EXIT_ERROR", "EXIT_LEGAL", "EXIT_NOT_LEGAL", "EXIT_OK", "main"]

if __name__ == "__main__":
    sys.exit(main())
