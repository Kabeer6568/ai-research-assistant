import asyncio
import json

import httpx
from pydantic import SecretStr

from app.config import Settings
from app.services import ai_provider

AsyncClient = httpx.AsyncClient


def test_gemini_batch_embeddings_use_native_endpoint(monkeypatch):
    requests_seen = []

    def handler(request):
        requests_seen.append(request)
        return httpx.Response(
            200,
            json={"embeddings": [{"values": [0.1, 0.2]}, {"values": [0.3, 0.4]}]},
        )

    monkeypatch.setattr(
        ai_provider,
        "get_settings",
        lambda: Settings(
            ai_base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ai_api_key=SecretStr("test-key"),
            ai_gemini_embedding_model="gemini-embedding-001",
        ),
    )
    monkeypatch.setattr(
        ai_provider.httpx,
        "AsyncClient",
        lambda **kwargs: AsyncClient(
            transport=httpx.MockTransport(handler),
            timeout=kwargs["timeout"],
        ),
    )

    embeddings = asyncio.run(
        ai_provider.embed_texts(["first excerpt", "second excerpt"], task_type="RETRIEVAL_DOCUMENT")
    )

    assert embeddings == [[0.1, 0.2], [0.3, 0.4]]
    request = requests_seen[0]
    assert request.url.path == "/v1beta/models/gemini-embedding-001:batchEmbedContents"
    assert request.headers["x-goog-api-key"] == "test-key"
    body = json.loads(request.content)
    assert body["requests"][0]["taskType"] == "RETRIEVAL_DOCUMENT"
    assert body["requests"][1]["content"]["parts"][0]["text"] == "second excerpt"


def test_openai_compatible_embedding_provider_keeps_existing_route(monkeypatch):
    requests_seen = []

    def handler(request):
        requests_seen.append(request)
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 0, "embedding": [0.1, 0.2]},
                    {"index": 1, "embedding": [0.3, 0.4]},
                ]
            },
        )

    monkeypatch.setattr(
        ai_provider,
        "get_settings",
        lambda: Settings(ai_base_url="https://api.example.test/v1"),
    )
    monkeypatch.setattr(
        ai_provider.httpx,
        "AsyncClient",
        lambda **kwargs: AsyncClient(
            transport=httpx.MockTransport(handler),
            timeout=kwargs["timeout"],
        ),
    )

    embeddings = asyncio.run(ai_provider.embed_texts(["first", "second"]))

    assert embeddings == [[0.1, 0.2], [0.3, 0.4]]
    assert requests_seen[0].url.path == "/v1/embeddings"
