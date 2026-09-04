from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Crew


class CrewRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, crew_id: str) -> Crew | None:
        statement = select(Crew).where(Crew.crew_id == crew_id)
        return self.session.scalar(statement)

    def get_all(self) -> list[Crew]:
        statement = select(Crew).order_by(Crew.crew_id)
        return list(self.session.scalars(statement).all())

    def get_by_base(self, base: str) -> list[Crew]:
        statement = (
            select(Crew)
            .where(Crew.base == base)
            .order_by(Crew.crew_id)
        )
        return list(self.session.scalars(statement).all())

    def get_by_status(self, status: str) -> list[Crew]:
        statement = (
            select(Crew)
            .where(Crew.status == status)
            .order_by(Crew.crew_id)
        )
        return list(self.session.scalars(statement).all())