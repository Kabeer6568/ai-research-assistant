from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    database_url = get_settings().database_url
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    if database_url.startswith("sqlite:///"):
        database_path = database_url.removeprefix("sqlite:///").split("?", maxsplit=1)[0]
        if database_path != ":memory:" and not database_path.startswith("/"):
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    with engine.begin() as connection:
        document_columns = {column["name"] for column in inspector.get_columns("documents")}
        if "index_status" not in document_columns:
            connection.execute(
                text("ALTER TABLE documents ADD COLUMN index_status VARCHAR(20) NOT NULL DEFAULT 'pending'")
            )
        if "index_error" not in document_columns:
            connection.execute(text("ALTER TABLE documents ADD COLUMN index_error TEXT"))
        message_columns = {column["name"] for column in inspector.get_columns("messages")}
        if "sources" not in message_columns:
            connection.execute(text("ALTER TABLE messages ADD COLUMN sources JSON"))
            connection.execute(text("UPDATE messages SET sources = '[]' WHERE sources IS NULL"))


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
