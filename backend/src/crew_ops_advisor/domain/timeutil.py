"""UTC time helpers.

The dataset is entirely UTC ("Z" suffixed ISO-8601) and the rulebook's rolling
windows are *calendar-day* windows, inclusive of the duty date. Everything here
is timezone-aware UTC; naive datetimes are never produced.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

ISO_Z = "%Y-%m-%dT%H:%M:%SZ"


def parse_utc(value: str) -> datetime:
    """Parse '2026-09-14T18:00:00Z' into an aware UTC datetime."""
    return datetime.strptime(value, ISO_Z).replace(tzinfo=UTC)


def fmt_utc(value: datetime) -> str:
    """Format an aware datetime as '2026-09-14T18:00:00Z'."""
    return value.astimezone(UTC).strftime(ISO_Z)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_hhmm(value: str) -> time:
    """Parse an on-call window boundary such as '06:00'."""
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes), tzinfo=UTC)


def hours_between(start: datetime, end: datetime) -> float:
    """Signed duration in hours (end - start)."""
    return (end - start).total_seconds() / 3600.0


def window_start(end: date, days: int) -> date:
    """First calendar day of a rolling window of `days` days ending on `end` (inclusive)."""
    return end - timedelta(days=days - 1)


def fmt_hours_hm(hours: float) -> str:
    """Render a duration like 1.33h as '1h20m' (minutes rounded)."""
    total_minutes = round(abs(hours) * 60)
    h, m = divmod(total_minutes, 60)
    sign = "-" if hours < 0 else ""
    return f"{sign}{h}h{m:02d}m"


def round2(value: float) -> float:
    return round(value + 0.0, 2)
