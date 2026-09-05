"""Proactive watchlist (ADR-0018 §2): what a controller should see before anyone asks.

Deterministic, no model involved. For a date (tomorrow by default):
  - crew within a margin of RULE-DUTY-02 / RULE-FLT-03 once that day's rostered duty counts;
  - certifications lapsing within a few days, flagged when the crew member is rostered on
    or after the expiry date (a RULE-CERT-06 breach waiting to happen);
  - the highest disruption-risk crew (a provided input, like a weather forecast).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from crew_ops_advisor.data import Datastore
from crew_ops_advisor.rules import checks
from crew_ops_advisor.simulation.engine import near_limits

DUTY_MARGIN_H = 10.0  # headroom under the 60 h / 7 d limit that earns a place on the list
FLIGHT_MARGIN_H = 10.0  # headroom under the 100 h / 28 d limit
TIGHT_DUTY_H = 4.0
TIGHT_FLIGHT_H = 4.0
CERT_DAYS = 7
TOP_RISK = 3
RISK_FLOOR = 0.5


def build_watchlist(
    store: Datastore,
    on: date,
    *,
    duty_margin_h: float = DUTY_MARGIN_H,
    flight_margin_h: float = FLIGHT_MARGIN_H,
    cert_days: int = CERT_DAYS,
    top_risk: int = TOP_RISK,
) -> dict[str, Any]:
    duty_limit = float(store.ruleset.param(checks.DUTY, "max_duty_hours"))
    flight_limit = float(store.ruleset.param(checks.FLT, "max_flight_hours"))

    limits = []
    for row in near_limits(
        store, on, max_duty_headroom=duty_margin_h, max_flight_headroom=flight_margin_h
    ):
        tight = row.duty_headroom <= TIGHT_DUTY_H or row.flight_headroom <= TIGHT_FLIGHT_H
        breach = row.duty_headroom < 0 or row.flight_headroom < 0
        if row.duty_headroom <= duty_margin_h:
            what = (
                f"{row.duty_hours_7d:.1f} h duty in 7 days through {on.isoformat()} — "
                f"{row.duty_headroom:.1f} h under the {duty_limit:.0f} h limit (RULE-DUTY-02)"
            )
            rule = "RULE-DUTY-02"
        else:
            what = (
                f"{row.flight_hours_28d:.1f} block hours in 28 days — "
                f"{row.flight_headroom:.1f} h under the {flight_limit:.0f} h limit (RULE-FLT-03)"
            )
            rule = "RULE-FLT-03"
        limits.append(
            {
                **row.to_dict(),
                "rule": rule,
                "severity": "breach" if breach else "tight" if tight else "watch",
                "note": what
                + (
                    f"; {row.planned_today:.1f} h rostered that day"
                    if row.planned_today
                    else "; nothing rostered that day"
                ),
            }
        )
    limits.sort(key=lambda r: (r["duty_headroom_7d"], r["flight_headroom_28d"], r["crew_id"]))

    certs = []
    for cert in store.certifications.expiring_between(on, on + timedelta(days=cert_days)):
        crew = store.crew.get(cert.crew_id)
        rostered_after = sorted(
            {
                d.date.isoformat()
                for d in store.pairings.duties_for_crew(cert.crew_id)
                if d.date > cert.valid_to
            }
        )
        certs.append(
            {
                "crew_id": cert.crew_id,
                "name": crew.name,
                "rank": crew.rank,
                "cert_type": cert.cert_type,
                "expires": cert.valid_to.isoformat(),
                "rostered_after_expiry": rostered_after,
                "rule": "RULE-CERT-06",
                "severity": "tight" if rostered_after else "watch",
                "note": f"{cert.cert_type.replace('_', ' ')} expires {cert.valid_to.isoformat()}"
                + (
                    f" — rostered on {', '.join(rostered_after)} after it lapses (RULE-CERT-06)"
                    if rostered_after
                    else " — no duty rostered after the expiry"
                ),
            }
        )
    certs.sort(key=lambda c: (c["expires"], c["crew_id"]))

    risks = []
    for signal in store.risk.list(min_score=RISK_FLOOR)[: max(0, top_risk)]:
        crew = store.crew.get(signal.crew_id)
        risks.append(
            {
                "crew_id": signal.crew_id,
                "name": crew.name,
                "rank": crew.rank,
                "disruption_risk_score": signal.disruption_risk_score,
                "drivers": list(signal.drivers),
                "severity": "watch",
                "note": f"disruption risk {signal.disruption_risk_score:.2f}: "
                + ", ".join(signal.drivers),
            }
        )

    total = len(limits) + len(certs) + len(risks)
    return {
        "date": on.isoformat(),
        "criteria": {
            "duty_headroom_h": duty_margin_h,
            "flight_headroom_h": flight_margin_h,
            "certification_days": cert_days,
            "top_risk": top_risk,
            "risk_floor": RISK_FLOOR,
        },
        "count": total,
        "near_limits": limits,
        "expiring_certifications": certs,
        "high_risk": risks,
        "rules": ["RULE-DUTY-02", "RULE-FLT-03", "RULE-CERT-06"],
    }
