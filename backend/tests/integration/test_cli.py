"""The `crew-ops` CLI: exit codes are a contract (0 legal, 1 not legal, 2 error)."""

import json
from pathlib import Path

import pytest

from crew_ops_advisor.__main__ import EXIT_ERROR, EXIT_LEGAL, EXIT_NOT_LEGAL, main

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

pytestmark = pytest.mark.usefixtures("cli_env")


@pytest.fixture
def cli_env(monkeypatch, db_path):
    monkeypatch.setenv("CREW_OPS_DB_PATH", str(db_path))
    monkeypatch.setenv("CREW_OPS_DATA_DIR", str(DATA_DIR))


def test_legal_cover_exits_zero(capsys):
    assert main(["check", "C-3310", "P-2291", "--callout"]) == EXIT_LEGAL
    out = capsys.readouterr().out
    assert out.startswith("C-3310 on 2026-09-15, 2026-09-16: LEGAL")
    assert "✗" not in out


def test_illegal_cover_exits_one_and_shows_breach(capsys):
    assert main(["check", "C-2087", "P-2291", "--from", "2026-09-15"]) == EXIT_NOT_LEGAL
    out = capsys.readouterr().out
    assert "NOT LEGAL" in out
    assert "✗ RULE-DUTY-02  RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15" in out


def test_json_output_is_the_evidence_object(capsys):
    assert main(["check", "C-2210", "P-2291", "--callout", "--json"]) == EXIT_LEGAL
    doc = json.loads(capsys.readouterr().out)
    assert doc["legal"] is True and doc["issues"] == []
    assert doc["conditions"] and "deadhead" in doc["conditions"][0]
    assert {v["rule_id"] for v in doc["verdicts"]} == set(doc["rules_checked"])


def test_rostered_flagged_exception(capsys):
    assert main(["rostered", "C-5417", "P-2213", "--on", "2026-09-19"]) == EXIT_NOT_LEGAL
    assert "recurrent_training expired 2026-09-17" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["check", "C-9999", "P-2291"], "unknown crew C-9999"),
        (["check", "C-3310", "P-0000"], "unknown pairing P-0000"),
        (["check", "C-3310", "P-2291", "--from", "2026-13-01"], "--from expects YYYY-MM-DD"),
        (["check", "C-3310", "P-2291", "--from", "2026-09-17"], "no duty days on or after"),
        (["rostered", "C-3310", "P-2291"], "not rostered on P-2291"),
    ],
)
def test_errors_exit_two_with_a_clean_message(capsys, argv, message):
    assert main(argv) == EXIT_ERROR
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error: ") and message in captured.err
    assert "Traceback" not in captured.err
