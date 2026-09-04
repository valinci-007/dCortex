from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DutyClock


class DutyClockRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_crew_id(self, crew_id: str) -> DutyClock | None:
        statement = select(DutyClock).where(DutyClock.crew_id == crew_id)
        return self.session.scalar(statement)

    def get_all(self) -> list[DutyClock]:
        statement = select(DutyClock).order_by(DutyClock.crew_id)
        return list(self.session.scalars(statement).all())