from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Certification


class CertificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_crew_id(self, crew_id: str) -> list[Certification]:
        statement = (
            select(Certification)
            .where(Certification.crew_id == crew_id)
            .order_by(Certification.cert_type)
        )
        return list(self.session.scalars(statement).all())

    def get_valid_on_date(
        self,
        crew_id: str,
        duty_date: date,
    ) -> list[Certification]:
        statement = (
            select(Certification)
            .where(
                Certification.crew_id == crew_id,
                Certification.valid_from <= duty_date,
                Certification.valid_to >= duty_date,
            )
            .order_by(Certification.cert_type)
        )
        return list(self.session.scalars(statement).all())