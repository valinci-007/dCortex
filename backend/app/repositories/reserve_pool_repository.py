from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ReservePool


class ReservePoolRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_crew_id(self, crew_id: str) -> ReservePool | None:
        statement = select(ReservePool).where(
            ReservePool.crew_id == crew_id
        )
        return self.session.scalar(statement)

    def get_by_base(self, base: str) -> list[ReservePool]:
        statement = (
            select(ReservePool)
            .where(ReservePool.base == base)
            .order_by(ReservePool.crew_id)
        )
        return list(self.session.scalars(statement).all())

    def get_available_on_date(
        self,
        base: str,
        reserve_date: date,
    ) -> list[ReservePool]:
        statement = (
            select(ReservePool)
            .where(ReservePool.base == base)
            .order_by(ReservePool.crew_id)
        )

        reserves = list(self.session.scalars(statement).all())

        return [
            reserve
            for reserve in reserves
            if reserve_date.isoformat() in reserve.dates
        ]