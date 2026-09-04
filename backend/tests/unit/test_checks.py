"""Pure-function tests for the seven rules, with hand-computed expectations."""

from datetime import date
from pathlib import Path

import pytest

from crew_ops_advisor.data import load_ruleset
from crew_ops_advisor.domain.models import Certification, Crew, DutyPeriod
from crew_ops_advisor.domain.timeutil import fmt_utc, parse_utc
from crew_ops_advisor.rules import VerdictStatus, checks

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture(scope="module")
def ruleset():
    return load_ruleset(DATA_DIR)


def duty(report: str, release: str, sectors: int = 4, **kw) -> DutyPeriod:
    defaults = dict(
        date=date.fromisoformat(report[:10]),
        report_utc=parse_utc(report),
        release_utc=parse_utc(release),
        flight_ids=tuple(f"DX40{i}-{report[:10]}" for i in range(1, sectors + 1)),
        flight_hours=2.0 * sectors,
        aircraft_type="A320",
        aircraft="VT-DXA",
        dep_station="BLR",
        arr_station="BLR",
        pairing_id="P-TEST",
    )
    defaults.update(kw)
    return DutyPeriod(**defaults)


CAPTAIN = Crew("C-0001", "T. Est", "Captain", "BLR", ("A320",), 10, 60, "active")


# ---- RULE-FDP-01 ------------------------------------------------------------


def test_fdp_limit_reduces_half_hour_per_sector_beyond_second(ruleset):
    assert checks.fdp_limit(1, ruleset) == 13.0
    assert checks.fdp_limit(2, ruleset) == 13.0
    assert checks.fdp_limit(3, ruleset) == 12.5
    assert checks.fdp_limit(4, ruleset) == 12.0


def test_fdp_pass_and_breach_use_q20_numbers(ruleset):
    ok = checks.check_fdp(duty("2026-09-16T01:30:00Z", "2026-09-16T12:45:00Z"), ruleset)
    assert ok.status is VerdictStatus.PASS and ok.computed == 11.25 and ok.limit == 12.0

    late = checks.check_fdp(duty("2026-09-16T01:30:00Z", "2026-09-16T14:15:00Z"), ruleset)
    assert late.status is VerdictStatus.BREACH
    assert late.computed == 12.75 and late.margin == -0.75
    assert late.detail == "RULE-FDP-01: duty runs 12.75h vs 12.0h limit (4 sectors)"


# ---- RULE-DUTY-02 / RULE-FLT-03 --------------------------------------------


def test_duty_window_sums_seven_calendar_days_inclusive(ruleset):
    totals = {date(2026, 9, d): 10.0 for d in range(8, 16)}  # 8 days of 10h
    v = checks.check_duty_window(totals, date(2026, 9, 14), ruleset)
    assert v.computed == 70.0 and v.status is VerdictStatus.BREACH
    assert v.detail == "RULE-DUTY-02: would exceed 60h/7d by 10h00m on 2026-09-14 (total 70.00h)"
    assert v.inputs["window_start"] == "2026-09-08"
    assert date(2026, 9, 15).isoformat() not in v.inputs["daily_duty_hours"]


def test_duty_window_pass_reports_headroom(ruleset):
    v = checks.check_duty_window({date(2026, 9, 14): 20.93}, date(2026, 9, 14), ruleset)
    assert v.status is VerdictStatus.PASS and v.margin == 39.07


def test_flight_window_breach_formats_like_duty(ruleset):
    totals = {date(2026, 9, 1): 101.5}
    v = checks.check_flight_window(totals, date(2026, 9, 14), ruleset)
    assert v.status is VerdictStatus.BREACH
    assert v.detail == "RULE-FLT-03: would exceed 100h/28d by 1h30m on 2026-09-14 (total 101.50h)"


# ---- RULE-REST-04 -----------------------------------------------------------


def test_rest_gap_downstream_conflict_matches_q28_wording(ruleset):
    prev = duty("2026-09-16T04:00:00Z", "2026-09-16T14:45:00Z", 3, pairing_id="P-2291")
    nxt = duty("2026-09-17T01:30:00Z", "2026-09-17T12:45:00Z", pairing_id="P-2204")
    v = checks.check_rest_gap(prev, nxt, ruleset, downstream=True)
    assert v.status is VerdictStatus.BREACH and v.computed == 10.75
    assert (
        v.detail
        == "RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"
    )


def test_rest_gap_exactly_twelve_hours_passes(ruleset):
    prev = duty("2026-09-16T04:00:00Z", "2026-09-16T15:30:00Z")
    nxt = duty("2026-09-17T03:30:00Z", "2026-09-17T12:00:00Z")
    assert checks.check_rest_gap(prev, nxt, ruleset, downstream=False).status is VerdictStatus.PASS


def test_rest_baseline_blocks_report_before_rest_completes(ruleset):
    d = duty("2026-09-15T06:00:00Z", "2026-09-15T15:30:00Z")
    early = checks.check_rest_baseline(d, parse_utc("2026-09-15T08:00:00Z"), ruleset)
    assert early.status is VerdictStatus.BREACH and "2h00m short" in early.detail
    fine = checks.check_rest_baseline(d, parse_utc("2026-09-15T02:00:00Z"), ruleset)
    assert fine.status is VerdictStatus.PASS


def test_earliest_next_report_is_release_plus_twelve(ruleset):
    # Q23: released 15:30Z on 16 Sep -> may report 03:30Z on 17 Sep
    assert (
        fmt_utc(checks.earliest_next_report(parse_utc("2026-09-16T15:30:00Z"), ruleset))
        == "2026-09-17T03:30:00Z"
    )


# ---- RULE-QUAL-05 / RULE-CERT-06 / RULE-BASE-07 ----------------------------


def test_rating_check():
    assert checks.check_rating(CAPTAIN, "A320").status is VerdictStatus.PASS
    v = checks.check_rating(CAPTAIN, "ATR72")
    assert (
        v.status is VerdictStatus.BREACH
        and v.detail == "RULE-QUAL-05: not rated on ATR72 (ratings: A320)"
    )


def test_certification_check_enforces_expiry_only():
    certs = [
        Certification(
            "C-5417", "licence", date(2027, 4, 11), date(2029, 4, 10)
        ),  # future valid_from: ignored
        Certification("C-5417", "recurrent_training", date(2025, 1, 7), date(2026, 9, 17)),
    ]
    assert checks.check_certifications(certs, date(2026, 9, 17)).status is VerdictStatus.PASS
    v = checks.check_certifications(certs, date(2026, 9, 19))
    assert v.status is VerdictStatus.BREACH
    assert v.detail == "RULE-CERT-06: recurrent_training expired 2026-09-17"


def test_base_check_is_conditional_off_base_for_callouts():
    assert checks.check_base(CAPTAIN, "BLR", callout=True).status is VerdictStatus.PASS
    off = checks.check_base(CAPTAIN, "DEL", callout=True)
    assert off.status is VerdictStatus.CONDITIONAL and off.passed
    assert checks.check_base(CAPTAIN, "DEL", callout=False).status is VerdictStatus.PASS
