from app.db.database import Base, engine
from app.models import (
    Certification,
    Crew,
    DutyClock,
    Flight,
    Pairing,
    ReservePool,
    RiskSignal,
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")