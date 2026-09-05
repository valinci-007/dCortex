"""The seven legality rules as pure functions.

Each function takes domain values plus the machine-readable parameters from
rules.json and returns a RuleVerdict. Nothing here touches I/O or the LLM.

Semantics follow rules.json and the organiser's validator exactly:
  * duty period = report -> release; FDP = its length in hours
  * rolling windows are calendar-day windows inclusive of the duty date
  * rest = next report - previous release
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime

from crew_ops_advisor.domain.models import Certification, Crew, DutyPeriod, Ruleset
from crew_ops_advisor.domain.timeutil import fmt_hours_hm, fmt_utc, hours_between, window_start
from crew_ops_advisor.rules.verdicts import RuleVerdict, VerdictStatus

_EPS = 1e-6

FDP = "RULE-FDP-01"
DUTY = "RULE-DUTY-02"
FLT = "RULE-FLT-03"
REST = "RULE-REST-04"
QUAL = "RULE-QUAL-05"
CERT = "RULE-CERT-06"
BASE = "RULE-BASE-07"


def fdp_limit(sectors: int, ruleset: Ruleset) -> float:
    base = float(ruleset.param(FDP, "base_fdp_hours"))
    reduction = float(ruleset.param(FDP, "reduction_per_extra_sector_hours"))
    free = int(ruleset.param(FDP, "free_sectors"))
    return base - reduction * max(0, sectors - free)


def check_fdp(duty: DutyPeriod, ruleset: Ruleset) -> RuleVerdict:
    """RULE-FDP-01: max flight duty period, reduced per sector beyond the free ones."""
    limit = fdp_limit(duty.sectors, ruleset)
    computed = round(duty.duty_hours, 2)
    inputs = {
        "report_utc": fmt_utc(duty.report_utc),
        "release_utc": fmt_utc(duty.release_utc),
        "sectors": duty.sectors,
        "flights": list(duty.flight_ids),
    }
    if duty.duty_hours > limit + _EPS:
        detail = f"{FDP}: duty runs {computed:.2f}h vs {limit:.1f}h limit ({duty.sectors} sectors)"
        status = VerdictStatus.BREACH
    else:
        detail = f"FDP {computed:.2f}h within the {limit:.1f}h limit for {duty.sectors} sectors"
        status = VerdictStatus.PASS
    return RuleVerdict(
        FDP,
        status,
        detail,
        date=duty.date,
        computed=computed,
        limit=limit,
        margin=round(limit - computed, 2),
        inputs=inputs,
    )


def _window_total(
    totals: Mapping[date, float], end: date, days: int
) -> tuple[float, dict[str, float]]:
    start = window_start(end, days)
    contributing = {
        d.isoformat(): round(v, 2)
        for d, v in sorted(totals.items())
        if start <= d <= end and abs(v) > _EPS
    }
    return sum(v for d, v in totals.items() if start <= d <= end), contributing


def check_duty_window(
    duty_by_date: Mapping[date, float], end: date, ruleset: Ruleset
) -> RuleVerdict:
    """RULE-DUTY-02: max duty hours in any N consecutive calendar days ending on `end`."""
    limit = float(ruleset.param(DUTY, "max_duty_hours"))
    days = int(ruleset.param(DUTY, "window_days"))
    total, contributing = _window_total(duty_by_date, end, days)
    computed = round(total, 2)
    inputs = {
        "window_start": window_start(end, days).isoformat(),
        "window_end": end.isoformat(),
        "daily_duty_hours": contributing,
    }
    if total > limit + _EPS:
        detail = (
            f"{DUTY}: would exceed {limit:.0f}h/{days}d by {fmt_hours_hm(computed - limit)} "
            f"on {end.isoformat()} (total {computed:.2f}h)"
        )
        status = VerdictStatus.BREACH
    else:
        detail = (
            f"{computed:.2f}h duty in the {days} days ending {end.isoformat()} "
            f"(limit {limit:.0f}h, headroom {limit - computed:.2f}h)"
        )
        status = VerdictStatus.PASS
    return RuleVerdict(
        DUTY,
        status,
        detail,
        date=end,
        computed=computed,
        limit=limit,
        margin=round(limit - computed, 2),
        inputs=inputs,
    )


def check_flight_window(
    flight_by_date: Mapping[date, float], end: date, ruleset: Ruleset
) -> RuleVerdict:
    """RULE-FLT-03: max block hours in any N consecutive calendar days ending on `end`."""
    limit = float(ruleset.param(FLT, "max_flight_hours"))
    days = int(ruleset.param(FLT, "window_days"))
    total, contributing = _window_total(flight_by_date, end, days)
    computed = round(total, 2)
    inputs = {
        "window_start": window_start(end, days).isoformat(),
        "window_end": end.isoformat(),
        "daily_flight_hours": contributing,
    }
    if total > limit + _EPS:
        detail = (
            f"{FLT}: would exceed {limit:.0f}h/{days}d by {fmt_hours_hm(computed - limit)} "
            f"on {end.isoformat()} (total {computed:.2f}h)"
        )
        status = VerdictStatus.BREACH
    else:
        detail = (
            f"{computed:.2f}h block in the {days} days ending {end.isoformat()} "
            f"(limit {limit:.0f}h, headroom {limit - computed:.2f}h)"
        )
        status = VerdictStatus.PASS
    return RuleVerdict(
        FLT,
        status,
        detail,
        date=end,
        computed=computed,
        limit=limit,
        margin=round(limit - computed, 2),
        inputs=inputs,
    )


def earliest_next_report(release_utc: datetime, ruleset: Ruleset) -> datetime:
    """RULE-REST-04 helper: release + minimum rest."""
    from datetime import timedelta

    return release_utc + timedelta(hours=float(ruleset.param(REST, "min_rest_hours")))


def check_rest_gap(
    prev: DutyPeriod, nxt: DutyPeriod, ruleset: Ruleset, *, downstream: bool
) -> RuleVerdict:
    """RULE-REST-04 between two consecutive duties. `downstream` marks a conflict with an
    already-rostered later duty (the proposed duty is `prev`)."""
    limit = float(ruleset.param(REST, "min_rest_hours"))
    gap = hours_between(prev.release_utc, nxt.report_utc)
    computed = round(gap, 2)
    inputs = {
        "previous_release_utc": fmt_utc(prev.release_utc),
        "next_report_utc": fmt_utc(nxt.report_utc),
        "previous": prev.label(),
        "next": nxt.label(),
    }
    if gap < limit - _EPS:
        if gap < 0:
            detail = (
                f"{REST}: {nxt.label()} on {nxt.date.isoformat()} overlaps {prev.label()} (no rest)"
            )
        elif downstream:
            detail = (
                f"{REST}: only {computed:.2f}h rest before {nxt.label()} on "
                f"{nxt.date.isoformat()} (downstream conflict)"
            )
        else:
            detail = (
                f"{REST}: only {computed:.2f}h rest after {prev.label()} "
                f"(released {fmt_utc(prev.release_utc)}) before reporting on {nxt.date.isoformat()}"
            )
        status = VerdictStatus.BREACH
    else:
        detail = (
            f"{computed:.2f}h rest between {prev.label()} ({prev.date.isoformat()}) and "
            f"{nxt.label()} ({nxt.date.isoformat()}); minimum {limit:.0f}h"
        )
        status = VerdictStatus.PASS
    return RuleVerdict(
        REST,
        status,
        detail,
        date=nxt.date,
        computed=computed,
        limit=limit,
        margin=round(gap - limit, 2),
        inputs=inputs,
    )


def check_rest_baseline(
    duty: DutyPeriod, last_rest_ended: datetime, ruleset: Ruleset
) -> RuleVerdict:
    """RULE-REST-04 for a duty with no earlier duty in the schedule: the crew may not report
    before the rest carried over from the snapshot has completed."""
    limit = float(ruleset.param(REST, "min_rest_hours"))
    slack = hours_between(last_rest_ended, duty.report_utc)
    inputs = {
        "earliest_report_utc": fmt_utc(last_rest_ended),
        "report_utc": fmt_utc(duty.report_utc),
    }
    if slack < -_EPS:
        detail = (
            f"{REST}: reports {fmt_utc(duty.report_utc)} before minimum rest completes at "
            f"{fmt_utc(last_rest_ended)} ({fmt_hours_hm(-slack)} short)"
        )
        status = VerdictStatus.BREACH
    else:
        detail = f"rest complete at {fmt_utc(last_rest_ended)}, {slack:.2f}h before report"
        status = VerdictStatus.PASS
    return RuleVerdict(
        REST,
        status,
        detail,
        date=duty.date,
        computed=round(slack, 2),
        limit=limit,
        margin=round(slack, 2),
        inputs=inputs,
    )


def check_rating(crew: Crew, aircraft_type: str) -> RuleVerdict:
    """RULE-QUAL-05: crew must hold a rating for the aircraft type."""
    inputs = {"aircraft_type": aircraft_type, "ratings": list(crew.ratings)}
    if aircraft_type in crew.ratings:
        return RuleVerdict(QUAL, VerdictStatus.PASS, f"rated on {aircraft_type}", inputs=inputs)
    return RuleVerdict(
        QUAL,
        VerdictStatus.BREACH,
        f"{QUAL}: not rated on {aircraft_type} (ratings: {', '.join(crew.ratings)})",
        inputs=inputs,
    )


def check_certifications(certs: Sequence[Certification], on: date) -> RuleVerdict:
    """RULE-CERT-06: all certifications valid on the duty date.

    Only expiry (`valid_to`) is enforced. The dataset's `valid_from` values are
    not reliable (some lie in the future for crew whose rosters are certified
    legal); the organiser's validator enforces expiry only, and so do we.
    """
    expired = sorted((c for c in certs if c.valid_to < on), key=lambda c: c.cert_type)
    inputs = {
        "date": on.isoformat(),
        "certifications": {c.cert_type: c.valid_to.isoformat() for c in certs},
    }
    if expired:
        parts = "; ".join(f"{c.cert_type} expired {c.valid_to.isoformat()}" for c in expired)
        return RuleVerdict(CERT, VerdictStatus.BREACH, f"{CERT}: {parts}", date=on, inputs=inputs)
    return RuleVerdict(
        CERT,
        VerdictStatus.PASS,
        f"all {len(certs)} certifications valid on {on.isoformat()}",
        date=on,
        inputs=inputs,
    )


def check_base(crew: Crew, dep_station: str, *, callout: bool) -> RuleVerdict:
    """RULE-BASE-07: callouts operate from own base unless deadhead positioning is applied."""
    inputs = {"base": crew.base, "duty_starts_at": dep_station, "callout": callout}
    if not callout:
        return RuleVerdict(
            BASE,
            VerdictStatus.PASS,
            "rostered duty — base rule applies to callouts only",
            inputs=inputs,
        )
    if crew.base == dep_station:
        return RuleVerdict(
            BASE, VerdictStatus.PASS, f"callout from own base {crew.base}", inputs=inputs
        )
    return RuleVerdict(
        BASE,
        VerdictStatus.CONDITIONAL,
        f"{BASE}: base {crew.base} ≠ duty start {dep_station}; "
        "deadhead positioning required (cost applies)",
        inputs=inputs,
    )
