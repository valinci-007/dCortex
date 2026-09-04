from sqlalchemy.orm import Session

from app.repositories import RiskSignalRepository


class RiskSignalService:
    def __init__(self, session: Session):
        self.repository = RiskSignalRepository(session)

    def get_risk_signal(self, crew_id: str):
        return self.repository.get_by_crew_id(crew_id)

    def list_high_risk(self, threshold: float = 0.7):
        return self.repository.get_high_risk(threshold)

    def list_risk_signals(self):
        return self.repository.get_all()