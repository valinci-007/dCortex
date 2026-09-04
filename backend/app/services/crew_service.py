from sqlalchemy.orm import Session

from app.repositories import CrewRepository


class CrewService:
    def __init__(self, session: Session):
        self.repository = CrewRepository(session)

    def get_crew(self, crew_id: str):
        return self.repository.get_by_id(crew_id)

    def list_crew(self):
        return self.repository.get_all()

    def list_by_base(self, base: str):
        return self.repository.get_by_base(base)

    def list_by_status(self, status: str):
        return self.repository.get_by_status(status)