from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RiskSignal


class RiskSignalRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_crew_id(self, crew_id: str) -> RiskSignal | None:
        statement = select(RiskSignal).where(
            RiskSignal.crew_id == crew_id
        )
        return self.session.scalar(statement)

    def get_high_risk(self, threshold: float = 0.7) -> list[RiskSignal]:
        statement = (
            select(RiskSignal)
            .where(RiskSignal.disruption_risk_score >= threshold)
            .order_by(RiskSignal.disruption_risk_score.desc())
        )
        return list(self.session.scalars(statement).all())

    def get_all(self) -> list[RiskSignal]:
        statement = select(RiskSignal).order_by(
            RiskSignal.disruption_risk_score.desc()
        )
        return list(self.session.scalars(statement).all())