from datetime import datetime

from sqlalchemy import DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RiskSignal(Base):
    __tablename__ = "risk_signals"

    crew_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    as_of_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    disruption_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    drivers: Mapped[list] = mapped_column(JSON, nullable=False)