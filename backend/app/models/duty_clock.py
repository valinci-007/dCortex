from datetime import datetime

from sqlalchemy import DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DutyClock(Base):
    __tablename__ = "duty_clocks"

    crew_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    as_of_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duty_hours_7d: Mapped[float] = mapped_column(Float, nullable=False)
    flight_hours_28d: Mapped[float] = mapped_column(Float, nullable=False)
    last_rest_ended: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    daily_history: Mapped[list] = mapped_column(JSON, nullable=False)