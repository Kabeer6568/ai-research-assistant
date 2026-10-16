def test_upload_rejects_non_pdf(client):
    client.post(
        "/api/auth/register",
        json={"email": "reader@example.com", "password": "safe-password-123"},
    )
    token_response = client.post(
        "/api/auth/login",
        data={"username": "reader@example.com", "password": "safe-password-123"},
    )
    headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
    response = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400
