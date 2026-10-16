from sqlalchemy import create_engine, inspect, text

from app import database


def test_existing_database_receives_additive_columns(tmp_path, monkeypatch):
    legacy_engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with legacy_engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE documents (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE conversations (id INTEGER PRIMARY KEY)"))
        connection.execute(
            text(
                "CREATE TABLE messages (id INTEGER PRIMARY KEY, conversation_id INTEGER, "
                "role VARCHAR(20), content TEXT, created_at DATETIME)"
            )
        )
    monkeypatch.setattr(database, "engine", legacy_engine)

    database.initialize_database()

    document_columns = {column["name"] for column in inspect(legacy_engine).get_columns("documents")}
    message_columns = {column["name"] for column in inspect(legacy_engine).get_columns("messages")}
    assert {"index_status", "index_error"} <= document_columns
    assert "sources" in message_columns
    legacy_engine.dispose()
