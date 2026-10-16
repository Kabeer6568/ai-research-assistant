def test_chat_requires_authentication(client):
    response = client.post("/api/chat/", json={"question": "What does the evidence say?"})
    assert response.status_code == 401


def test_chat_reports_unconfigured_ai_services(client, monkeypatch):
    from app.config import Settings

    monkeypatch.setattr(
        "app.services.ai_provider.get_settings",
        lambda: Settings(ai_base_url=None),
    )
    client.post(
        "/api/auth/register",
        json={"email": "reader@example.com", "password": "safe-password-123"},
    )
    token_response = client.post(
        "/api/auth/login",
        data={"username": "reader@example.com", "password": "safe-password-123"},
    )
    headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}

    response = client.post("/api/chat/", headers=headers, json={"question": "What does the evidence say?"})

    assert response.status_code == 503
    assert client.get("/api/conversations/", headers=headers).json() == []
