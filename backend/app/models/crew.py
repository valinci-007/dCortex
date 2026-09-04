from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Crew(Base):
    __tablename__ = "crew"

    crew_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rank: Mapped[str] = mapped_column(String(50), nullable=False)
    base: Mapped[str] = mapped_column(String(10), nullable=False)
    ratings: Mapped[list] = mapped_column(JSON, nullable=False)
    seniority: Mapped[int] = mapped_column(Integer, nullable=False)
    reachability_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)