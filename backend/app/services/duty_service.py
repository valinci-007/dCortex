from sqlalchemy.orm import Session

from app.repositories import DutyClockRepository


class DutyService:
    def __init__(self, session: Session):
        self.repository = DutyClockRepository(session)

    def get_duty_status(self, crew_id: str):
        return self.repository.get_by_crew_id(crew_id)

    def list_duty_statuses(self):
        return self.repository.get_all()