from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Pairing


class PairingRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, pairing_id: str) -> Pairing | None:
        statement = select(Pairing).where(
            Pairing.pairing_id == pairing_id
        )
        return self.session.scalar(statement)

    def get_all(self) -> list[Pairing]:
        statement = select(Pairing).order_by(Pairing.pairing_id)
        return list(self.session.scalars(statement).all())

    def get_by_crew_id(self, crew_id: str) -> list[Pairing]:
        statement = select(Pairing).order_by(Pairing.pairing_id)
        pairings = list(self.session.scalars(statement).all())

        return [
            pairing
            for pairing in pairings
            if any(
                crew_member.get("crew_id") == crew_id
                for crew_member in pairing.crew
            )
        ]

    def get_by_date(self, pairing_date: date) -> list[Pairing]:
        statement = select(Pairing).order_by(Pairing.pairing_id)
        pairings = list(self.session.scalars(statement).all())

        return [
            pairing
            for pairing in pairings
            if any(
                day.get("date") == pairing_date.isoformat()
                for day in pairing.days
            )
        ]