from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Flight


class FlightRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, flight_id: str) -> Flight | None:
        statement = select(Flight).where(Flight.flight_id == flight_id)
        return self.session.scalar(statement)

    def get_all(self) -> list[Flight]:
        statement = select(Flight).order_by(Flight.date, Flight.dep_utc)
        return list(self.session.scalars(statement).all())

    def get_by_date(self, flight_date: date) -> list[Flight]:
        statement = (
            select(Flight)
            .where(Flight.date == flight_date)
            .order_by(Flight.dep_utc)
        )
        return list(self.session.scalars(statement).all())

    def get_by_station(self, station: str) -> list[Flight]:
        statement = (
            select(Flight)
            .where(Flight.dep_station == station)
            .order_by(Flight.date, Flight.dep_utc)
        )
        return list(self.session.scalars(statement).all())

    def get_by_aircraft_type(self, aircraft_type: str) -> list[Flight]:
        statement = (
            select(Flight)
            .where(Flight.aircraft_type == aircraft_type)
            .order_by(Flight.date, Flight.dep_utc)
        )
        return list(self.session.scalars(statement).all())