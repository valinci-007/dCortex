from datetime import date

from sqlalchemy.orm import Session

from app.repositories import FlightRepository


class FlightService:
    def __init__(self, session: Session):
        self.repository = FlightRepository(session)

    def get_flight(self, flight_id: str):
        return self.repository.get_by_id(flight_id)

    def list_flights(self):
        return self.repository.get_all()

    def list_by_date(self, flight_date: date):
        return self.repository.get_by_date(flight_date)

    def list_departures(self, station: str):
        return self.repository.get_by_station(station)

    def list_by_aircraft_type(self, aircraft_type: str):
        return self.repository.get_by_aircraft_type(aircraft_type)