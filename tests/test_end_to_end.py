from io import BytesIO

from pypdf import PdfWriter
from sqlalchemy import select

from app.database import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services import document_service, rag_service
from app.services import retrieval_service
from app.services.vector_store import search_chunks


def create_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def register_and_login(client, email="researcher@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": "correct-horse-battery"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_upload_retrieve_chat_and_history(client, monkeypatch):
    async def fake_embeddings(texts):
        return [[1.0, 0.0] for _ in texts]

    async def fake_completion(messages):
        assert "[S1]" in messages[-1]["content"]
        return "Green space supports wellbeing [S1]."

    monkeypatch.setattr(document_service, "extract_pdf_text", lambda _: "Urban green spaces support wellbeing.")
    monkeypatch.setattr(document_service, "embed_texts", fake_embeddings)
    monkeypatch.setattr(retrieval_service, "embed_texts", fake_embeddings)
    monkeypatch.setattr(rag_service, "generate_completion", fake_completion)

    headers = register_and_login(client)
    upload = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("green-space.pdf", create_pdf(), "application/pdf")},
    )

    assert upload.status_code == 201
    document = upload.json()
    assert document["index_status"] == "indexed"

    answer = client.post(
        "/api/chat/",
        headers=headers,
        json={"question": "What does the research say about wellbeing?"},
    )
    assert answer.status_code == 200
    answer_data = answer.json()
    assert answer_data["answer"].endswith("[S1].")
    assert answer_data["sources"][0]["filename"] == "green-space.pdf"
    assert answer_data["sources"][0]["excerpt"] == "Urban green spaces support wellbeing."

    second_headers = register_and_login(client, "second-researcher@example.com")
    second_user = client.get("/api/documents/", headers=second_headers)
    assert second_user.json() == []
    with SessionLocal() as database:
        second_user_id = database.scalar(
            select(User.id).where(User.email == "second-researcher@example.com")
        )
        assert search_chunks(database, [1.0, 0.0], second_user_id) == []

    follow_up = client.post(
        "/api/chat/",
        headers=headers,
        json={
            "question": "What is one implication?",
            "conversation_id": answer_data["conversation_id"],
        },
    )
    assert follow_up.status_code == 200

    history = client.get(
        f"/api/conversations/{answer_data['conversation_id']}/messages",
        headers=headers,
    )
    assert history.status_code == 200
    assert len(history.json()) == 4
    assert history.json()[1]["sources"][0]["citation"] == "S1"

    deleted = client.delete(f"/api/documents/{document['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/api/documents/", headers=headers).json() == []
    with SessionLocal() as database:
        assert database.scalars(
            select(DocumentChunk).where(DocumentChunk.document_id == document["id"])
        ).all() == []


def test_documents_and_conversations_are_private(client):
    first_headers = register_and_login(client, "first@example.com")
    second_headers = register_and_login(client, "second@example.com")
    conversation = client.post(
        "/api/conversations/",
        headers=first_headers,
        json={"title": "Private notes"},
    )
    conversation_id = conversation.json()["id"]

    assert client.get("/api/conversations/", headers=second_headers).json() == []
    assert client.get(
        f"/api/conversations/{conversation_id}/messages",
        headers=second_headers,
    ).status_code == 404
    assert client.delete(
        f"/api/conversations/{conversation_id}",
        headers=second_headers,
    ).status_code == 404
