from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings


def build_database_url() -> str:
    if settings.DB_TYPE.lower() == "sqlite":
        db_path = Path(settings.DB_NAME)
        if not db_path.is_absolute():
            db_path = Path(__file__).resolve().parents[1] / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    return (
        "postgresql+psycopg2://"
        f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/"
        f"{settings.POSTGRES_DB}"
    )


DATABASE_URL = build_database_url()
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False}
    if settings.DB_TYPE.lower() == "sqlite"
    else {},
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_engine():
    return engine
