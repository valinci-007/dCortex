"""Build the SQLite database from the dataset JSON files.

`data/*.json` is the source of truth. The database is rebuilt from scratch on
every call (the dataset is < 1 MB), so it is always consistent with the JSON.
Referential integrity is enforced by the schema's foreign keys: a dangling
crew or flight reference in the JSON fails the build instead of surfacing
later as a wrong answer.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from crew_ops_advisor.config import DATASET_FILES
from crew_ops_advisor.data.db import apply_schema, connect, table_count

_COST_KEYS = (
    "reserve_callout_pilot",
    "reserve_callout_cabin",
    "dayoff_callout_pilot",
    "dayoff_callout_cabin",
    "deadhead_positioning",
    "delay_cost_per_duty_hour",
    "cancellation_per_flight",
    "hotel_overnight",
)


@dataclass(frozen=True, slots=True)
class BuildReport:
    db_path: Path
    counts: dict[str, int]

    def summary(self) -> str:
        parts = ", ".join(f"{k}={v}" for k, v in self.counts.items())
        return f"{self.db_path}: {parts}"


def _read_json(data_dir: Path, name: str) -> Any:
    with (data_dir / name).open() as fh:
        return json.load(fh)


def is_stale(data_dir: Path, db_path: Path) -> bool:
    """True when the database is missing or older than any dataset file."""
    if not db_path.exists():
        return True
    built = db_path.stat().st_mtime
    return any(
        (data_dir / f).stat().st_mtime > built for f in DATASET_FILES if (data_dir / f).exists()
    )


def build_database(data_dir: Path, db_path: Path) -> BuildReport:
    """Create `db_path` from the JSON files in `data_dir`, replacing any existing file.

    The build happens in a temporary file next to the target and is moved into
    place atomically, so a failed build never leaves a half-written database.
    """
    data_dir = Path(data_dir)
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(prefix=".crew_ops-", suffix=".db", dir=db_path.parent)
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        conn = connect(tmp_path)
        try:
            apply_schema(conn)
            with conn:
                _load_all(conn, data_dir)
            counts = {
                "crew": table_count(conn, "crew"),
                "flights": table_count(conn, "flights"),
                "pairings": table_count(conn, "pairings"),
                "reserves": table_count(conn, "reserves"),
                "certifications": table_count(conn, "certifications"),
            }
        finally:
            conn.close()
        os.replace(tmp_path, db_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    return BuildReport(db_path=db_path, counts=counts)


def ensure_database(data_dir: Path, db_path: Path, *, force: bool = False) -> BuildReport | None:
    """Build the database if it is missing/stale (or when forced). Returns the report if built."""
    if force or is_stale(data_dir, db_path):
        return build_database(data_dir, db_path)
    return None


def _load_all(conn: sqlite3.Connection, data_dir: Path) -> None:
    _load_crew(conn, _read_json(data_dir, "crew.json"))
    _load_flights(conn, _read_json(data_dir, "flights.json"))
    _load_rosters(conn, _read_json(data_dir, "rosters.json"))
    _load_duty_clocks(conn, _read_json(data_dir, "duty_clocks.json"))
    _load_reserves(conn, _read_json(data_dir, "reserve_pool.json"))
    _load_certifications(conn, _read_json(data_dir, "certifications.json"))
    _load_risk_signals(conn, _read_json(data_dir, "risk_signals.json"))
    _load_costs(conn, _read_json(data_dir, "costs.json"))
    _load_meta(conn, data_dir)


def _load_crew(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    conn.executemany(
        "INSERT INTO crew VALUES (:crew_id, :name, :rank, :base, :seniority, "
        ":reachability_minutes, :status)",
        rows,
    )
    conn.executemany(
        "INSERT INTO crew_ratings VALUES (?, ?)",
        [(c["crew_id"], r) for c in rows for r in c["ratings"]],
    )


def _load_flights(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    conn.executemany(
        "INSERT INTO flights VALUES (:flight_id, :flight_no, :date, :dep_station, :arr_station, "
        ":dep_utc, :arr_utc, :block_hours, :aircraft, :aircraft_type, :seats)",
        rows,
    )


def _load_rosters(conn: sqlite3.Connection, doc: dict[str, Any]) -> None:
    for p in doc["pairings"]:
        conn.execute("INSERT INTO pairings VALUES (?, ?)", (p["pairing_id"], p["aircraft"]))
        for day in p["days"]:
            conn.execute(
                "INSERT INTO pairing_days VALUES (?, ?, ?, ?)",
                (p["pairing_id"], day["date"], day["report_utc"], day["release_utc"]),
            )
            conn.executemany(
                "INSERT INTO pairing_day_flights VALUES (?, ?, ?, ?)",
                [(p["pairing_id"], day["date"], i, fid) for i, fid in enumerate(day["flights"])],
            )
        conn.executemany(
            "INSERT INTO pairing_crew VALUES (?, ?, ?)",
            [(p["pairing_id"], m["crew_id"], m["role"]) for m in p["crew"]],
        )
    conn.executemany(
        "INSERT INTO flagged_exceptions VALUES (:crew_id, :date, :rule, :note)",
        doc.get("flagged_exceptions", []),
    )


def _load_duty_clocks(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    conn.executemany(
        "INSERT INTO duty_clocks VALUES (:crew_id, :as_of_utc, :duty_hours_7d, "
        ":flight_hours_28d, :last_rest_ended)",
        rows,
    )
    conn.executemany(
        "INSERT INTO duty_daily VALUES (?, ?, ?, ?)",
        [
            (c["crew_id"], d["date"], d["duty_hours"], d["flight_hours"])
            for c in rows
            for d in c["daily_history"]
        ],
    )


def _load_reserves(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    for r in rows:
        conn.execute(
            "INSERT INTO reserves VALUES (?, ?, ?, ?, ?)",
            (
                r["crew_id"],
                r["base"],
                r["oncall_window_utc"]["start"],
                r["oncall_window_utc"]["end"],
                r.get("note", ""),
            ),
        )
        conn.executemany(
            "INSERT INTO reserve_dates VALUES (?, ?)", [(r["crew_id"], d) for d in r["dates"]]
        )


def _load_certifications(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    conn.executemany(
        "INSERT INTO certifications VALUES (:crew_id, :cert_type, :valid_from, :valid_to)", rows
    )


def _load_risk_signals(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    conn.executemany(
        "INSERT INTO risk_signals VALUES (:crew_id, :as_of_utc, :disruption_risk_score)", rows
    )
    conn.executemany(
        "INSERT INTO risk_drivers VALUES (?, ?, ?)",
        [(r["crew_id"], i, d) for r in rows for i, d in enumerate(r["drivers"])],
    )


def _load_costs(conn: sqlite3.Connection, doc: dict[str, Any]) -> None:
    conn.executemany("INSERT INTO costs VALUES (?, ?)", [(k, float(doc[k])) for k in _COST_KEYS])
    conn.execute("INSERT INTO meta VALUES ('currency', ?)", (doc["currency"],))
    conn.execute("INSERT INTO meta VALUES ('cost_notes', ?)", (doc.get("notes", ""),))


def _load_meta(conn: sqlite3.Connection, data_dir: Path) -> None:
    snapshot = conn.execute("SELECT MAX(as_of_utc) FROM duty_clocks").fetchone()[0]
    conn.execute("INSERT INTO meta VALUES ('snapshot_utc', ?)", (snapshot,))
    conn.execute("INSERT INTO meta VALUES ('data_dir', ?)", (str(data_dir),))
