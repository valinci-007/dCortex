import json
import sys
from datetime import date, datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete

from app.db.database import SessionLocal
from app.models import (
    Certification,
    Crew,
    DutyClock,
    Flight,
    Pairing,
    ReservePool,
    RiskSignal,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def load_json(filename: str):
    with (DATA_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def clear_tables(session) -> None:
    session.execute(delete(Certification))
    session.execute(delete(Crew))
    session.execute(delete(DutyClock))
    session.execute(delete(Flight))
    session.execute(delete(Pairing))
    session.execute(delete(ReservePool))
    session.execute(delete(RiskSignal))


def load_crew(session) -> None:
    records = load_json("crew.json")

    for record in records:
        session.add(
            Crew(
                crew_id=record["crew_id"],
                name=record["name"],
                rank=record["rank"],
                base=record["base"],
                ratings=record["ratings"],
                seniority=record["seniority"],
                reachability_minutes=record["reachability_minutes"],
                status=record["status"],
            )
        )


def load_flights(session) -> None:
    records = load_json("flights.json")

    for record in records:
        session.add(
            Flight(
                flight_id=record["flight_id"],
                flight_no=record["flight_no"],
                date=parse_date(record["date"]),
                dep_station=record["dep_station"],
                arr_station=record["arr_station"],
                dep_utc=parse_datetime(record["dep_utc"]),
                arr_utc=parse_datetime(record["arr_utc"]),
                block_hours=record["block_hours"],
                aircraft=record["aircraft"],
                aircraft_type=record["aircraft_type"],
                seats=record["seats"],
            )
        )


def load_duty_clocks(session) -> None:
    records = load_json("duty_clocks.json")

    for record in records:
        session.add(
            DutyClock(
                crew_id=record["crew_id"],
                as_of_utc=parse_datetime(record["as_of_utc"]),
                duty_hours_7d=record["duty_hours_7d"],
                flight_hours_28d=record["flight_hours_28d"],
                last_rest_ended=parse_datetime(record["last_rest_ended"]),
                daily_history=record["daily_history"],
            )
        )


def load_certifications(session) -> None:
    records = load_json("certifications.json")

    for record in records:
        session.add(
            Certification(
                crew_id=record["crew_id"],
                cert_type=record["cert_type"],
                valid_from=parse_date(record["valid_from"]),
                valid_to=parse_date(record["valid_to"]),
            )
        )


def load_reserve_pool(session) -> None:
    records = load_json("reserve_pool.json")

    for record in records:
        session.add(
            ReservePool(
                crew_id=record["crew_id"],
                base=record["base"],
                dates=record["dates"],
                oncall_window_utc=record["oncall_window_utc"],
                note=record["note"],
            )
        )


def load_risk_signals(session) -> None:
    records = load_json("risk_signals.json")

    for record in records:
        session.add(
            RiskSignal(
                crew_id=record["crew_id"],
                as_of_utc=parse_datetime(record["as_of_utc"]),
                disruption_risk_score=record["disruption_risk_score"],
                drivers=record["drivers"],
            )
        )


def load_pairings(session) -> None:
    data = load_json("rosters.json")

    for record in data["pairings"]:
        session.add(
            Pairing(
                pairing_id=record["pairing_id"],
                aircraft=record["aircraft"],
                days=record["days"],
                crew=record["crew"],
            )
        )


def main() -> None:
    session = SessionLocal()

    try:
        clear_tables(session)

        load_crew(session)
        load_flights(session)
        load_duty_clocks(session)
        load_certifications(session)
        load_reserve_pool(session)
        load_risk_signals(session)
        load_pairings(session)

        session.commit()

        print("Dataset loaded successfully.")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()