"""
This module provides utility functions for managing database connections and sessions.
"""
import sqlmodel
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlmodel import Session

DATABASE_URL = "sqlite:///backend.db"

def get_engine() -> Engine:
    """
    Creates a SQLAlchemy engine.
    """
    return create_engine(DATABASE_URL, echo=True)

def get_db() -> Generator[Session, None, None]:
    """
    Retrieves a new SQLAlchemy Session from the connection pool.
    :yield: SQLAlchemy Session
    """
    engine = get_engine()
    with Session(engine) as session:
        yield session

@contextmanager
def get_database_session() -> Generator[Session, None, None]:
    """
    Context manager for database session
    :yield: SQLAlchemy Session
    """
    engine = get_engine()
    with Session(engine) as session:
        yield session
        