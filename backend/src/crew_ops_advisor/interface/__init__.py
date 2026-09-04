"""Interfaces: the CLI (dev harness) now; the local HTTP API for the React UI in P3."""

from crew_ops_advisor.interface.cli import EXIT_ERROR, EXIT_LEGAL, EXIT_NOT_LEGAL, EXIT_OK, main

__all__ = ["EXIT_ERROR", "EXIT_LEGAL", "EXIT_NOT_LEGAL", "EXIT_OK", "main"]
