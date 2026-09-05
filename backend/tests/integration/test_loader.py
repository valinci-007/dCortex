"""The SQLite build must reproduce the dataset exactly and refuse inconsistent input."""

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from crew_ops_advisor.data import build_database, ensure_database
from crew_ops_advisor.data.db import connect, table_count
from crew_ops_advisor.domain.timeutil import fmt_utc

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_counts_match_dataset_readme(db_path):
    conn = connect(db_path)
    try:
        assert table_count(conn, "flights") == 147
        assert table_count(conn, "crew") == 150
        assert table_count(conn, "pairings") == 39
        assert table_count(conn, "reserves") == 16
        assert table_count(conn, "certifications") == 600
        assert table_count(conn, "duty_daily") == 150 * 28
        assert table_count(conn, "flagged_exceptions") == 1
        assert table_count(conn, "risk_signals") == 150
    finally:
        conn.close()


def test_snapshot_and_costs(store):
    assert fmt_utc(store.snapshot_utc) == "2026-09-14T18:00:00Z"
    costs = store.costs
    assert costs.currency == "INR"
    assert costs.reserve_callout_pilot == 18500
    assert costs.deadhead_positioning == 6500
    assert costs.delay_cost_per_duty_hour == 5400
    assert costs.cancellation_per_flight == 250000


def test_every_flight_is_covered_by_exactly_one_pairing(db_path):
    conn = connect(db_path)
    try:
        uncovered = conn.execute(
            "SELECT COUNT(*) FROM flights f WHERE NOT EXISTS "
            "(SELECT 1 FROM pairing_day_flights p WHERE p.flight_id = f.flight_id)"
        ).fetchone()[0]
        duplicates = conn.execute(
            "SELECT COUNT(*) FROM (SELECT flight_id FROM pairing_day_flights "
            "GROUP BY flight_id HAVING COUNT(*) > 1)"
        ).fetchone()[0]
    finally:
        conn.close()
    assert uncovered == 0 and duplicates == 0


def test_dangling_reference_fails_the_build(tmp_path):
    """A roster entry naming an unknown crew member must abort the build, not load silently."""
    broken = tmp_path / "data"
    shutil.copytree(DATA_DIR, broken)
    rosters = json.loads((broken / "rosters.json").read_text())
    rosters["pairings"][0]["crew"][0]["crew_id"] = "C-0000"
    (broken / "rosters.json").write_text(json.dumps(rosters))

    target = tmp_path / "broken.db"
    with pytest.raises(sqlite3.IntegrityError):
        build_database(broken, target)
    assert not target.exists()
    assert not list(tmp_path.glob(".crew_ops-*.db"))


def test_ensure_database_rebuilds_only_when_stale(tmp_path):
    target = tmp_path / "x.db"
    assert ensure_database(DATA_DIR, target) is not None
    assert ensure_database(DATA_DIR, target) is None
    assert ensure_database(DATA_DIR, target, force=True) is not None
