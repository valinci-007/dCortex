from datetime import UTC, date, datetime

from crew_ops_advisor.domain.timeutil import (
    fmt_hours_hm,
    fmt_utc,
    hours_between,
    parse_hhmm,
    parse_utc,
    window_start,
)


def test_parse_and_format_roundtrip():
    dt = parse_utc("2026-09-14T18:00:00Z")
    assert dt == datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
    assert fmt_utc(dt) == "2026-09-14T18:00:00Z"


def test_hours_between_is_signed():
    a, b = parse_utc("2026-09-16T15:30:00Z"), parse_utc("2026-09-17T01:30:00Z")
    assert hours_between(a, b) == 10.0
    assert hours_between(b, a) == -10.0


def test_window_start_is_inclusive_of_end():
    assert window_start(date(2026, 9, 14), 7) == date(2026, 9, 8)
    assert window_start(date(2026, 9, 14), 28) == date(2026, 8, 18)


def test_fmt_hours_hm_matches_answer_key_style():
    assert fmt_hours_hm(1.33) == "1h20m"
    assert fmt_hours_hm(1.08) == "1h05m"
    assert fmt_hours_hm(8.25) == "8h15m"
    assert fmt_hours_hm(0.0) == "0h00m"


def test_parse_hhmm_is_utc_aware():
    t = parse_hhmm("06:00")
    assert (t.hour, t.minute) == (6, 0)
    assert t.tzinfo is UTC
