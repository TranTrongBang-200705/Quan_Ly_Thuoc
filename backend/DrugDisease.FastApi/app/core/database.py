from __future__ import annotations

from collections.abc import Generator
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_database_engine() -> Engine:
    first_engine: Engine | None = None

    for server, database_url in settings.sqlalchemy_database_urls:
        candidate_engine = create_engine(
            database_url,
            pool_pre_ping=True,
            future=True,
        )

        if first_engine is None:
            first_engine = candidate_engine

        try:
            with candidate_engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            logger.info("Connected to SQL Server using server '%s'.", server)
            return candidate_engine
        except SQLAlchemyError:
            logger.exception("Cannot connect to SQL Server using server '%s'.", server)

            if candidate_engine is not first_engine:
                candidate_engine.dispose()

    if first_engine is None:
        raise RuntimeError("No SQL Server database URL was configured.")

    logger.error("All SQL Server connection attempts failed. Keeping the first engine for request-time retries.")
    return first_engine


engine = create_database_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError:
        logger.exception("Database error while handling request.")
        db.rollback()
        raise
    finally:
        db.close()
