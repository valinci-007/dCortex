"""Datastore facade: one object bundling the SQLite repositories, the ruleset,
costs and the snapshot time. Everything above the data layer receives a
Datastore and never sees a connection.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from crew_ops_advisor.config import Settings
from crew_ops_advisor.data.db import connect
from crew_ops_advisor.data.loader import ensure_database
from crew_ops_advisor.data.repositories import (
    CertificationRepository,
    CostRepository,
    CrewRepository,
    DutyClockRepository,
    FlightRepository,
    PairingRepository,
    ReserveRepository,
    RiskRepository,
)
from crew_ops_advisor.domain.models import CostConfig, RuleDef, Ruleset
from crew_ops_advisor.domain.timeutil import parse_utc


def load_ruleset(data_dir: Path) -> Ruleset:
    with (Path(data_dir) / "rules.json").open() as fh:
        doc = json.load(fh)
    rules = {
        r["rule_id"]: RuleDef(
            rule_id=r["rule_id"], text=r["text"], params=dict(r.get("params", {}))
        )
        for r in doc["rules"]
    }
    return Ruleset(
        time_convention=doc.get("time_convention", ""),
        definitions=dict(doc.get("definitions", {})),
        rules=rules,
    )


def load_json(data_dir: Path, name: str) -> Any:
    """Raw access to answer-key files (questions.json, scenarios.json) for the eval harness."""
    with (Path(data_dir) / name).open() as fh:
        return json.load(fh)


class Datastore:
    def __init__(self, conn: sqlite3.Connection, data_dir: Path):
        self._conn = conn
        self.data_dir = Path(data_dir)
        self.crew = CrewRepository(conn)
        self.flights = FlightRepository(conn)
        self.pairings = PairingRepository(conn, self.flights)
        self.duty_clocks = DutyClockRepository(conn)
        self.reserves = ReserveRepository(conn)
        self.certifications = CertificationRepository(conn)
        self.risk = RiskRepository(conn)
        self._costs = CostRepository(conn)
        self.ruleset: Ruleset = load_ruleset(self.data_dir)
        meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM meta")}
        self.snapshot_utc: datetime = parse_utc(meta["snapshot_utc"])

    @classmethod
    def open(cls, settings: Settings | None = None, *, rebuild: bool = False) -> Datastore:
        """Open (building or refreshing the SQLite file first when needed)."""
        settings = settings or Settings.from_env()
        ensure_database(settings.data_dir, settings.db_path, force=rebuild)
        return cls(connect(settings.db_path), settings.data_dir)

    @property
    def costs(self) -> CostConfig:
        return self._costs.get()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Datastore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
