from datetime import date

from sqlalchemy.orm import Session

from app.repositories import CertificationRepository


class CertificationService:
    def __init__(self, session: Session):
        self.repository = CertificationRepository(session)

    def get_certifications(self, crew_id: str):
        return self.repository.get_by_crew_id(crew_id)

    def get_valid_certifications(
        self,
        crew_id: str,
        duty_date: date,
    ):
        return self.repository.get_valid_on_date(crew_id, duty_date)