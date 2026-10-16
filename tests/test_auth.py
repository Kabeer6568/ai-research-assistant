def test_register_login_and_protected_endpoint(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "researcher@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201

    response = client.post(
        "/api/auth/login",
        data={"username": "researcher@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = client.get("/api/documents/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_duplicate_registration_is_rejected(client):
    user = {"email": "reader@example.com", "password": "safe-password-123"}
    assert client.post("/api/auth/register", json=user).status_code == 201
    assert client.post("/api/auth/register", json=user).status_code == 409
