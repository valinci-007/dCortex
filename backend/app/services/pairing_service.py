from datetime import date

from sqlalchemy.orm import Session

from app.repositories import PairingRepository


class PairingService:
    def __init__(self, session: Session):
        self.repository = PairingRepository(session)

    def get_pairing(self, pairing_id: str):
        return self.repository.get_by_id(pairing_id)

    def list_pairings(self):
        return self.repository.get_all()

    def list_by_crew(self, crew_id: str):
        return self.repository.get_by_crew_id(crew_id)

    def list_by_date(self, pairing_date: date):
        return self.repository.get_by_date(pairing_date)