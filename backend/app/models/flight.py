from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Flight(Base):
    __tablename__ = "flights"

    flight_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    flight_no: Mapped[str] = mapped_column(String(20), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    dep_station: Mapped[str] = mapped_column(String(10), nullable=False)
    arr_station: Mapped[str] = mapped_column(String(10), nullable=False)
    dep_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    arr_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    block_hours: Mapped[float] = mapped_column(Float, nullable=False)
    aircraft: Mapped[str] = mapped_column(String(20), nullable=False)
    aircraft_type: Mapped[str] = mapped_column(String(20), nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=False)