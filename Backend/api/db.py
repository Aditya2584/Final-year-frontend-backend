import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def _default_db_url() -> str:
    # Production-friendly:
    # - set DATABASE_URL to Postgres/MySQL when deploying
    # - default to local SQLite for easy dev
    return os.getenv("DATABASE_URL", "sqlite:///./app.db")


DATABASE_URL = _default_db_url()


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    from api.models import Appointment  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

