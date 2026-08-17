"""
Database Connection and Initialization.

This module sets up the SQLite engine and provides the session dependency 
for the FastAPI endpoints.
"""
import os
from sqlmodel import SQLModel, create_engine, Session

os.makedirs("data", exist_ok=True)
sqlite_file_name = "data/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    """Creates the SQLite database and all SQLModel tables if they do not exist."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """FastAPI Dependency for database sessions. Yields a session per request."""
    with Session(engine) as session:
        yield session
