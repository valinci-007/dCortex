"""Proactive watchlist (ADR-0018 §2): deterministic alerts for a date."""

from __future__ import annotations

from datetime import date

from crew_ops_advisor.simulation.watchlist import build_watchlist


def test_watchlist_for_tomorrow_flags_limits_lapsing_certs_and_risk(store):
    w = build_watchlist(store, date(2026, 9, 15))
    assert w["date"] == "2026-09-15" and w["count"] == (
        len(w["near_limits"]) + len(w["expiring_certifications"]) + len(w["high_risk"])
    )
    near = {r["crew_id"]: r for r in w["near_limits"]}
    assert "C-2087" in near and near["C-2087"]["rule"] == "RULE-DUTY-02"
    assert near["C-2087"]["duty_headroom_7d"] < 10 and "RULE-DUTY-02" in near["C-2087"]["note"]
    assert w["near_limits"] == sorted(w["near_limits"], key=lambda r: r["duty_headroom_7d"])

    certs = {c["crew_id"]: c for c in w["expiring_certifications"]}
    # C-5417's recurrent training lapses on 17 Sep while a duty is rostered on 19 Sep
    assert certs["C-5417"]["severity"] == "tight"
    assert certs["C-5417"]["rostered_after_expiry"] == ["2026-09-19"]
    assert "RULE-CERT-06" in certs["C-5417"]["note"]

    assert 1 <= len(w["high_risk"]) <= 3
    assert all(r["disruption_risk_score"] >= 0.5 for r in w["high_risk"])
    scores = [r["disruption_risk_score"] for r in w["high_risk"]]
    assert scores == sorted(scores, reverse=True)
    assert w["uncovered_flights"] == []


def test_watchlist_margins_are_configurable(store):
    strict = build_watchlist(store, date(2026, 9, 15), duty_margin_h=1.0, cert_days=1, top_risk=1)
    assert strict["near_limits"] == []
    assert strict["expiring_certifications"] == []
    assert len(strict["high_risk"]) == 1


def test_watchlist_tool_defaults_to_tomorrow(registry):
    out = registry.call("watchlist", {})
    assert out.ok and out.result["date"] == "2026-09-15"
    out = registry.call("watchlist", {"date": "2026-09-17", "duty_headroom_hours": 20})
    assert out.ok and out.result["date"] == "2026-09-17"
