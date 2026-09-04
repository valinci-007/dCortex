from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Pairing(Base):
    __tablename__ = "pairings"

    pairing_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    aircraft: Mapped[str] = mapped_column(String(20), nullable=False)
    days: Mapped[list] = mapped_column(JSON, nullable=False)
    crew: Mapped[list] = mapped_column(JSON, nullable=False)