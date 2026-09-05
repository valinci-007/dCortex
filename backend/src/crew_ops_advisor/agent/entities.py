"""Entity extraction from controller questions: ids, stations, dates, ranks, routes.

Used by the offline router (which has no model to do this for it). Everything
resolves against the dataset — station codes come from the schedule, relative
dates from the snapshot — so nothing is guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from crew_ops_advisor.data import Datastore

CREW_RE = re.compile(r"\bC-\d{4}\b", re.I)
PAIRING_RE = re.compile(r"\bP-\d{4}\b", re.I)
FLIGHT_RE = re.compile(r"\bDX\d{3}\b", re.I)
AIRCRAFT_RE = re.compile(r"\bVT-[A-Z]{3}\b", re.I)
RULE_RE = re.compile(r"\bRULE-[A-Z]+-\d{2}\b", re.I)
ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
DAY_MONTH_RE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"
    r"(?:\s+(\d{4}))?\b",
    re.I,
)
DAY_RANGE_RE = re.compile(
    r"\b(\d{1,2})\s*[–-]\s*(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b",
    re.I,
)
MONTH_DAY_RE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?"
    r"(?:,?\s+(\d{4}))?\b",
    re.I,
)
WITHIN_DAYS_RE = re.compile(
    r"\b(?:within|next|in|over)\s+(?:the\s+)?(?:next\s+)?(\d{1,3})\s+days?\b", re.I
)
TIME_WINDOW_RE = re.compile(
    r"\b(\d{1,2}):(\d{2})\s*(?:z|utc)?\s*[–\-to]+\s*(\d{1,2}):(\d{2})\s*(?:z|utc)?\b", re.I
)

_MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    )
}
_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

CITY_TO_STATION = {
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "madras": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "kochi": "COK",
    "cochin": "COK",
    "goa": "GOI",
}

RANK_PATTERNS = (
    ("Senior Cabin Crew", re.compile(r"\bsenior cabin crew\b|\bscc\b|\bpurser\b", re.I)),
    ("First Officer", re.compile(r"\bfirst officers?\b|\bfos?\b(?!\w)|\bf/o\b", re.I)),
    ("Captain", re.compile(r"\bcaptains?\b|\bcapts?\b|\bcpts?\b", re.I)),
    ("Cabin Crew", re.compile(r"\bcabin crew\b|\bflight attendants?\b", re.I)),
)


@dataclass(frozen=True, slots=True)
class Entities:
    crew_ids: tuple[str, ...] = ()
    pairing_ids: tuple[str, ...] = ()
    flight_nos: tuple[str, ...] = ()
    aircraft: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    stations: tuple[str, ...] = ()  # in order of appearance
    dates: tuple[date, ...] = ()
    ranks: tuple[str, ...] = ()
    within_days: int | None = None
    time_window: tuple[str, str] | None = None  # ("08:00", "14:00")
    dep_station: str | None = None
    arr_station: str | None = None
    flags: frozenset[str] = field(default_factory=frozenset)  # today/tomorrow/afternoon/...

    @property
    def crew_id(self) -> str | None:
        return self.crew_ids[0] if self.crew_ids else None

    @property
    def date(self) -> date | None:
        return self.dates[0] if self.dates else None


class EntityExtractor:
    def __init__(self, store: Datastore):
        self.snapshot_date: date = store.snapshot_utc.date()
        self.stations: tuple[str, ...] = tuple(store.flights.stations())
        self._station_re = re.compile(r"\b(" + "|".join(self.stations) + r")\b")
        self._city_re = re.compile(
            r"\b(" + "|".join(sorted(CITY_TO_STATION, key=len, reverse=True)) + r")\b", re.I
        )

    # ---- dates -------------------------------------------------------------

    def dates(self, text: str) -> tuple[date, ...]:
        found: list[tuple[int, date]] = []
        for m in ISO_DATE_RE.finditer(text):
            try:
                found.append((m.start(), date(int(m[1]), int(m[2]), int(m[3]))))
            except ValueError:
                continue
        for m in DAY_RANGE_RE.finditer(text):
            found.append((m.start(), self._dm(int(m[1]), m[3], None)))
            found.append((m.start() + 1, self._dm(int(m[2]), m[3], None)))
        for m in DAY_MONTH_RE.finditer(text):
            found.append((m.start(), self._dm(int(m[1]), m[2], m[3])))
        for m in MONTH_DAY_RE.finditer(text):
            found.append((m.start(), self._dm(int(m[2]), m[1], m[3])))
        low = text.lower()
        rel = {
            "day after tomorrow": 2,
            "tomorrow": 1,
            "today": 0,
            "tonight": 0,
            "yesterday": -1,
        }
        for word, delta in rel.items():
            idx = low.find(word)
            if idx >= 0 and not (
                word in ("today", "tomorrow") and "day after tomorrow" in low and word == "tomorrow"
            ):
                found.append((idx, self.snapshot_date + timedelta(days=delta)))
        for i, name in enumerate(_WEEKDAYS):
            idx = low.find(name)
            if idx >= 0:
                ahead = (i - self.snapshot_date.weekday()) % 7
                found.append((idx, self.snapshot_date + timedelta(days=ahead)))
        out: list[date] = []
        for _, d in sorted(found):
            if d not in out:
                out.append(d)
        return tuple(out)

    def _dm(self, day: int, month: str, year: str | None) -> date:
        m = _MONTHS[month[:3].lower()]
        y = int(year) if year else self.snapshot_date.year
        try:
            return date(y, m, day)
        except ValueError:
            return self.snapshot_date

    # ---- everything ----------------------------------------------------------

    def extract(self, text: str) -> Entities:
        low = text.lower()
        stations_in_order: list[tuple[int, str]] = []
        for m in self._station_re.finditer(text):
            stations_in_order.append((m.start(), m[1]))
        for m in self._city_re.finditer(text):
            stations_in_order.append((m.start(), CITY_TO_STATION[m[1].lower()]))
        stations = tuple(dict.fromkeys(s for _, s in sorted(stations_in_order)))
        dep, arr = self._route(text, low, stations)

        ranks = tuple(rank for rank, pat in RANK_PATTERNS if pat.search(text))
        # "cabin crew" also matches inside "senior cabin crew": keep only the senior form then
        if (
            "Senior Cabin Crew" in ranks
            and "Cabin Crew" in ranks
            and not re.search(r"(?<!senior )cabin crew", low)
        ):
            ranks = tuple(r for r in ranks if r != "Cabin Crew")

        within = WITHIN_DAYS_RE.search(text)
        window = TIME_WINDOW_RE.search(text)
        flags = {
            w
            for w in ("today", "tomorrow", "afternoon", "morning", "evening", "tonight", "week")
            if w in low
        }

        return Entities(
            crew_ids=tuple(dict.fromkeys(m.group().upper() for m in CREW_RE.finditer(text))),
            pairing_ids=tuple(dict.fromkeys(m.group().upper() for m in PAIRING_RE.finditer(text))),
            flight_nos=tuple(dict.fromkeys(m.group().upper() for m in FLIGHT_RE.finditer(text))),
            aircraft=tuple(dict.fromkeys(m.group().upper() for m in AIRCRAFT_RE.finditer(text))),
            rule_ids=tuple(dict.fromkeys(m.group().upper() for m in RULE_RE.finditer(text))),
            stations=stations,
            dates=self.dates(text),
            ranks=ranks,
            within_days=int(within[1]) if within else None,
            time_window=(f"{int(window[1]):02d}:{window[2]}", f"{int(window[3]):02d}:{window[4]}")
            if window
            else None,
            dep_station=dep,
            arr_station=arr,
            flags=frozenset(flags),
        )

    def _route(
        self, text: str, low: str, stations: tuple[str, ...]
    ) -> tuple[str | None, str | None]:
        if not stations:
            return None, None
        if len(stations) >= 2:
            a, b = stations[0], stations[1]
            # "from B to A" / "A→B" / "A-B" / "A to B" all read departure first
            if re.search(rf"\b(?:to|into|arriv\w*)\s+(?:at\s+)?{a}\b", text) and not re.search(
                rf"\b(?:to|into)\s+{b}\b", text
            ):
                return b, a
            return a, b
        s = stations[0]
        if re.search(rf"\b(?:arriv\w*|into|land\w*|inbound)\s+(?:at\s+|in\s+)?{s}\b", text, re.I):
            return None, s
        if re.search(rf"\bto\s+{s}\b", text) and not re.search(
            rf"\b(?:from|depart\w*|out of|leav\w*)\s+{s}\b", text, re.I
        ):
            return None, s
        return s, None
