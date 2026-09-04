"""Data layer: SQLite built from data/*.json, and typed repositories over it."""

from crew_ops_advisor.data.loader import BuildReport, build_database, ensure_database
from crew_ops_advisor.data.repositories import NotFoundError
from crew_ops_advisor.data.store import Datastore, load_json, load_ruleset

__all__ = [
    "BuildReport",
    "Datastore",
    "NotFoundError",
    "build_database",
    "ensure_database",
    "load_json",
    "load_ruleset",
]
