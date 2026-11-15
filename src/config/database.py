from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config.settings import get_settings

settings = get_settings()

# Configure engine arguments; handle SQLite specially if used in test environments
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a SQLAlchemy database session for each request."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
