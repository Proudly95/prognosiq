def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={"email": "dev@test.com", "password": "secret123", "full_name": "Dev"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "dev@test.com"
    assert "password_hash" not in body


def test_register_duplicate_email(client):
    payload = {"email": "dup@test.com", "password": "secret123", "full_name": "Dup"}
    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Email already registered"


def test_register_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "secret123", "full_name": "Dev"},
    )
    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "123", "full_name": "Dev"}
    )
    assert response.status_code == 422
