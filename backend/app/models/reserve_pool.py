from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ReservePool(Base):
    __tablename__ = "reserve_pool"

    crew_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    base: Mapped[str] = mapped_column(String(10), nullable=False)
    dates: Mapped[list] = mapped_column(JSON, nullable=False)
    oncall_window_utc: Mapped[dict] = mapped_column(JSON, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)