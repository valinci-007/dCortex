"""Shared fixtures: one SQLite build per test session from the repo's data/."""

from __future__ import annotations

from pathlib import Path

import pytest

from crew_ops_advisor.data import Datastore, build_database

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"


@pytest.fixture(scope="session")
def db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("db") / "crew_ops.db"
    build_database(DATA_DIR, path)
    return path


@pytest.fixture(scope="session")
def store(db_path: Path):
    from crew_ops_advisor.data.db import connect

    ds = Datastore(connect(db_path), DATA_DIR)
    yield ds
    ds.close()


@pytest.fixture(scope="session")
def registry(store):
    from crew_ops_advisor.tools import build_registry

    return build_registry(store)


@pytest.fixture(scope="session")
def offline_advisor(store, registry):
    from crew_ops_advisor.agent import Advisor, OfflineProvider

    return Advisor(store, registry, OfflineProvider(store))
