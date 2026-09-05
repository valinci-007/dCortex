"""Repositories: SQLite rows -> typed domain objects.

This module is the only place (besides the loader) that knows SQL. Everything
above it — rules, simulation, tools — works on domain objects.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Sequence
from datetime import date, datetime

from crew_ops_advisor.domain.models import (
    Certification,
    CostConfig,
    Crew,
    DailyDuty,
    DutyClock,
    DutyPeriod,
    FlaggedException,
    Flight,
    Pairing,
    PairingCrew,
    PairingDay,
    ReserveEntry,
    RiskSignal,
)
from crew_ops_advisor.domain.timeutil import parse_date, parse_hhmm, parse_utc


class NotFoundError(LookupError):
    """Raised when an identifier does not exist in the dataset."""


# ----------------------------------------------------------------- row mappers


def _crew(row: sqlite3.Row, ratings: Sequence[str]) -> Crew:
    return Crew(
        crew_id=row["crew_id"],
        name=row["name"],
        rank=row["rank"],
        base=row["base"],
        ratings=tuple(ratings),
        seniority=int(row["seniority"]),
        reachability_minutes=int(row["reachability_minutes"]),
        status=row["status"],
    )


def _flight(row: sqlite3.Row) -> Flight:
    return Flight(
        flight_id=row["flight_id"],
        flight_no=row["flight_no"],
        date=parse_date(row["date"]),
        dep_station=row["dep_station"],
        arr_station=row["arr_station"],
        dep_utc=parse_utc(row["dep_utc"]),
        arr_utc=parse_utc(row["arr_utc"]),
        block_hours=float(row["block_hours"]),
        aircraft=row["aircraft"],
        aircraft_type=row["aircraft_type"],
        seats=int(row["seats"]),
    )


# ----------------------------------------------------------------- repositories


class CrewRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def _ratings(self, crew_ids: Iterable[str]) -> dict[str, list[str]]:
        ids = list(crew_ids)
        if not ids:
            return {}
        marks = ",".join("?" * len(ids))
        out: dict[str, list[str]] = {cid: [] for cid in ids}
        for r in self._conn.execute(
            f"SELECT crew_id, rating FROM crew_ratings WHERE crew_id IN ({marks}) ORDER BY rating",
            ids,
        ):
            out[r["crew_id"]].append(r["rating"])
        return out

    def _hydrate(self, rows: Sequence[sqlite3.Row]) -> list[Crew]:
        ratings = self._ratings(r["crew_id"] for r in rows)
        return [_crew(r, ratings[r["crew_id"]]) for r in rows]

    def get(self, crew_id: str) -> Crew:
        row = self._conn.execute("SELECT * FROM crew WHERE crew_id = ?", (crew_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"unknown crew {crew_id}")
        return self._hydrate([row])[0]

    def exists(self, crew_id: str) -> bool:
        return (
            self._conn.execute("SELECT 1 FROM crew WHERE crew_id = ?", (crew_id,)).fetchone()
            is not None
        )

    def list(
        self,
        *,
        base: str | None = None,
        rank: str | None = None,
        status: str | None = None,
        rating: str | None = None,
    ) -> list[Crew]:
        sql = "SELECT c.* FROM crew c"
        where, args = [], []
        if rating is not None:
            sql += " JOIN crew_ratings cr ON cr.crew_id = c.crew_id AND cr.rating = ?"
            args.append(rating)
        for col, val in (("base", base), ("rank", rank), ("status", status)):
            if val is not None:
                where.append(f"c.{col} = ?")
                args.append(val)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY c.crew_id"
        return self._hydrate(self._conn.execute(sql, args).fetchall())

    def search_name(self, fragment: str) -> list[Crew]:
        rows = self._conn.execute(
            "SELECT * FROM crew WHERE name LIKE ? ORDER BY crew_id", (f"%{fragment}%",)
        ).fetchall()
        return self._hydrate(rows)


class FlightRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get(self, flight_id: str) -> Flight:
        row = self._conn.execute(
            "SELECT * FROM flights WHERE flight_id = ?", (flight_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"unknown flight {flight_id}")
        return _flight(row)

    def get_many(self, flight_ids: Sequence[str]) -> list[Flight]:
        """Flights in the order requested."""
        return [self.get(fid) for fid in flight_ids]

    def by_number(self, flight_no: str, on: date) -> Flight | None:
        row = self._conn.execute(
            "SELECT * FROM flights WHERE flight_no = ? AND date = ?", (flight_no, on.isoformat())
        ).fetchone()
        return _flight(row) if row else None

    def list(
        self,
        *,
        on: date | None = None,
        dep_station: str | None = None,
        arr_station: str | None = None,
        aircraft: str | None = None,
        aircraft_type: str | None = None,
        dep_from: datetime | None = None,
        dep_to: datetime | None = None,
    ) -> list[Flight]:
        where, args = [], []
        if on is not None:
            where.append("date = ?")
            args.append(on.isoformat())
        for col, val in (
            ("dep_station", dep_station),
            ("arr_station", arr_station),
            ("aircraft", aircraft),
            ("aircraft_type", aircraft_type),
        ):
            if val is not None:
                where.append(f"{col} = ?")
                args.append(val)
        if dep_from is not None:
            where.append("dep_utc >= ?")
            args.append(dep_from.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if dep_to is not None:
            where.append("dep_utc <= ?")
            args.append(dep_to.strftime("%Y-%m-%dT%H:%M:%SZ"))
        sql = "SELECT * FROM flights"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY dep_utc, flight_no"
        return [_flight(r) for r in self._conn.execute(sql, args)]

    def stations(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT dep_station AS s FROM flights "
            "UNION SELECT DISTINCT arr_station FROM flights ORDER BY 1"
        ).fetchall()
        return [r[0] for r in rows]

    def aircraft(self) -> list[tuple[str, str]]:
        """(registration, type) pairs in the schedule."""
        rows = self._conn.execute(
            "SELECT DISTINCT aircraft, aircraft_type FROM flights ORDER BY aircraft"
        ).fetchall()
        return [(r[0], r[1]) for r in rows]


class PairingRepository:
    def __init__(self, conn: sqlite3.Connection, flights: FlightRepository):
        self._conn = conn
        self._flights = flights

    def _hydrate(self, pairing_id: str, aircraft: str) -> Pairing:
        days = []
        for d in self._conn.execute(
            "SELECT date, report_utc, release_utc FROM pairing_days "
            "WHERE pairing_id = ? ORDER BY date",
            (pairing_id,),
        ):
            fids = [
                r["flight_id"]
                for r in self._conn.execute(
                    "SELECT flight_id FROM pairing_day_flights WHERE pairing_id = ? AND date = ? "
                    "ORDER BY position",
                    (pairing_id, d["date"]),
                )
            ]
            days.append(
                PairingDay(
                    date=parse_date(d["date"]),
                    flight_ids=tuple(fids),
                    report_utc=parse_utc(d["report_utc"]),
                    release_utc=parse_utc(d["release_utc"]),
                )
            )
        crew = [
            PairingCrew(crew_id=r["crew_id"], role=r["role"])
            for r in self._conn.execute(
                "SELECT crew_id, role FROM pairing_crew WHERE pairing_id = ? ORDER BY rowid",
                (pairing_id,),
            )
        ]
        return Pairing(pairing_id=pairing_id, aircraft=aircraft, days=tuple(days), crew=tuple(crew))

    def get(self, pairing_id: str) -> Pairing:
        row = self._conn.execute(
            "SELECT pairing_id, aircraft FROM pairings WHERE pairing_id = ?", (pairing_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"unknown pairing {pairing_id}")
        return self._hydrate(row["pairing_id"], row["aircraft"])

    def list(self) -> list[Pairing]:
        rows = self._conn.execute(
            "SELECT pairing_id, aircraft FROM pairings ORDER BY pairing_id"
        ).fetchall()
        return [self._hydrate(r["pairing_id"], r["aircraft"]) for r in rows]

    def for_crew(self, crew_id: str) -> list[Pairing]:
        rows = self._conn.execute(
            "SELECT p.pairing_id, p.aircraft FROM pairings p JOIN pairing_crew pc "
            "ON pc.pairing_id = p.pairing_id WHERE pc.crew_id = ? ORDER BY p.pairing_id",
            (crew_id,),
        ).fetchall()
        return [self._hydrate(r["pairing_id"], r["aircraft"]) for r in rows]

    def for_flight(self, flight_id: str) -> Pairing | None:
        row = self._conn.execute(
            "SELECT p.pairing_id, p.aircraft FROM pairings p JOIN pairing_day_flights f "
            "ON f.pairing_id = p.pairing_id WHERE f.flight_id = ?",
            (flight_id,),
        ).fetchone()
        return self._hydrate(row["pairing_id"], row["aircraft"]) if row else None

    def for_aircraft_on(self, aircraft: str, on: date) -> Pairing | None:
        row = self._conn.execute(
            "SELECT p.pairing_id, p.aircraft FROM pairings p JOIN pairing_days d "
            "ON d.pairing_id = p.pairing_id WHERE p.aircraft = ? AND d.date = ?",
            (aircraft, on.isoformat()),
        ).fetchone()
        return self._hydrate(row["pairing_id"], row["aircraft"]) if row else None

    def flagged_exceptions(self) -> list[FlaggedException]:
        return [
            FlaggedException(
                crew_id=r["crew_id"], date=parse_date(r["date"]), rule=r["rule"], note=r["note"]
            )
            for r in self._conn.execute("SELECT * FROM flagged_exceptions ORDER BY date, crew_id")
        ]

    # ---- derived duty periods --------------------------------------------

    def duty_period(self, pairing: Pairing, day: PairingDay) -> DutyPeriod:
        legs = self._flights.get_many(day.flight_ids)
        return DutyPeriod(
            date=day.date,
            report_utc=day.report_utc,
            release_utc=day.release_utc,
            flight_ids=day.flight_ids,
            flight_hours=round(sum(f.block_hours for f in legs), 2),
            aircraft_type=legs[0].aircraft_type,
            aircraft=pairing.aircraft,
            dep_station=legs[0].dep_station,
            arr_station=legs[-1].arr_station,
            pairing_id=pairing.pairing_id,
        )

    def duty_periods(self, pairing: Pairing, *, from_date: date | None = None) -> list[DutyPeriod]:
        return [
            self.duty_period(pairing, d)
            for d in pairing.days
            if from_date is None or d.date >= from_date
        ]

    def duties_for_crew(self, crew_id: str) -> list[DutyPeriod]:
        """Every rostered duty period for a crew member in the schedule week, chronological."""
        duties = [dp for p in self.for_crew(crew_id) for dp in self.duty_periods(p)]
        duties.sort(key=lambda d: d.report_utc)
        return duties


class DutyClockRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get(self, crew_id: str) -> DutyClock:
        row = self._conn.execute(
            "SELECT * FROM duty_clocks WHERE crew_id = ?", (crew_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"no duty clock for {crew_id}")
        history = tuple(
            DailyDuty(
                date=parse_date(r["date"]),
                duty_hours=float(r["duty_hours"]),
                flight_hours=float(r["flight_hours"]),
            )
            for r in self._conn.execute(
                "SELECT date, duty_hours, flight_hours FROM duty_daily "
                "WHERE crew_id = ? ORDER BY date",
                (crew_id,),
            )
        )
        return DutyClock(
            crew_id=crew_id,
            as_of_utc=parse_utc(row["as_of_utc"]),
            duty_hours_7d=float(row["duty_hours_7d"]),
            flight_hours_28d=float(row["flight_hours_28d"]),
            last_rest_ended=parse_utc(row["last_rest_ended"]),
            daily_history=history,
        )

    def all_summaries(self) -> list[DutyClock]:
        """Clocks without daily history (cheap), for ranking/filtering across crew."""
        return [
            DutyClock(
                crew_id=r["crew_id"],
                as_of_utc=parse_utc(r["as_of_utc"]),
                duty_hours_7d=float(r["duty_hours_7d"]),
                flight_hours_28d=float(r["flight_hours_28d"]),
                last_rest_ended=parse_utc(r["last_rest_ended"]),
                daily_history=(),
            )
            for r in self._conn.execute("SELECT * FROM duty_clocks ORDER BY crew_id")
        ]


class ReserveRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def _hydrate(self, row: sqlite3.Row) -> ReserveEntry:
        dates = tuple(
            parse_date(r["date"])
            for r in self._conn.execute(
                "SELECT date FROM reserve_dates WHERE crew_id = ? ORDER BY date", (row["crew_id"],)
            )
        )
        return ReserveEntry(
            crew_id=row["crew_id"],
            base=row["base"],
            dates=dates,
            oncall_start=parse_hhmm(row["oncall_start"]),
            oncall_end=parse_hhmm(row["oncall_end"]),
            note=row["note"],
        )

    def get(self, crew_id: str) -> ReserveEntry | None:
        row = self._conn.execute("SELECT * FROM reserves WHERE crew_id = ?", (crew_id,)).fetchone()
        return self._hydrate(row) if row else None

    def list(self, *, base: str | None = None, on: date | None = None) -> list[ReserveEntry]:
        sql = "SELECT DISTINCT r.* FROM reserves r"
        where, args = [], []
        if on is not None:
            sql += " JOIN reserve_dates d ON d.crew_id = r.crew_id AND d.date = ?"
            args.append(on.isoformat())
        if base is not None:
            where.append("r.base = ?")
            args.append(base)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY r.crew_id"
        return [self._hydrate(r) for r in self._conn.execute(sql, args).fetchall()]


class CertificationRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    @staticmethod
    def _hydrate(r: sqlite3.Row) -> Certification:
        return Certification(
            crew_id=r["crew_id"],
            cert_type=r["cert_type"],
            valid_from=parse_date(r["valid_from"]),
            valid_to=parse_date(r["valid_to"]),
        )

    def for_crew(self, crew_id: str) -> list[Certification]:
        rows = self._conn.execute(
            "SELECT * FROM certifications WHERE crew_id = ? ORDER BY cert_type", (crew_id,)
        ).fetchall()
        return [self._hydrate(r) for r in rows]

    def expiring_between(self, start: date, end: date) -> list[Certification]:
        rows = self._conn.execute(
            "SELECT * FROM certifications WHERE valid_to BETWEEN ? AND ? "
            "ORDER BY valid_to, crew_id",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [self._hydrate(r) for r in rows]


class RiskRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def _hydrate(self, row: sqlite3.Row) -> RiskSignal:
        drivers = tuple(
            r["driver"]
            for r in self._conn.execute(
                "SELECT driver FROM risk_drivers WHERE crew_id = ? ORDER BY position",
                (row["crew_id"],),
            )
        )
        return RiskSignal(
            crew_id=row["crew_id"],
            as_of_utc=parse_utc(row["as_of_utc"]),
            disruption_risk_score=float(row["disruption_risk_score"]),
            drivers=drivers,
        )

    def get(self, crew_id: str) -> RiskSignal:
        row = self._conn.execute(
            "SELECT * FROM risk_signals WHERE crew_id = ?", (crew_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"no risk signal for {crew_id}")
        return self._hydrate(row)

    def list(self, *, min_score: float = 0.0) -> list[RiskSignal]:
        rows = self._conn.execute(
            "SELECT * FROM risk_signals WHERE disruption_risk_score >= ? "
            "ORDER BY disruption_risk_score DESC, crew_id",
            (min_score,),
        ).fetchall()
        return [self._hydrate(r) for r in rows]


class CostRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def get(self) -> CostConfig:
        values = {
            r["key"]: float(r["value"]) for r in self._conn.execute("SELECT key, value FROM costs")
        }
        meta = {r["key"]: r["value"] for r in self._conn.execute("SELECT key, value FROM meta")}
        return CostConfig(currency=meta["currency"], notes=meta.get("cost_notes", ""), **values)
