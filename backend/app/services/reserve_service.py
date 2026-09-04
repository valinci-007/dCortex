from datetime import date

from sqlalchemy.orm import Session

from app.repositories import ReservePoolRepository


class ReserveService:
    def __init__(self, session: Session):
        self.repository = ReservePoolRepository(session)

    def get_reserve_crew(self, crew_id: str):
        return self.repository.get_by_crew_id(crew_id)

    def list_by_base(self, base: str):
        return self.repository.get_by_base(base)

    def list_available_on_date(
        self,
        base: str,
        reserve_date: date,
    ):
        return self.repository.get_available_on_date(
            base,
            reserve_date,
        )