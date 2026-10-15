def register_and_login(client, email="user@test.com") -> dict:
    reg = client.post(
        "/auth/register",
        json={"email": email, "password": "secret123", "full_name": "Test User"},
    )
    assert reg.status_code in (201, 409), f"register failed: {reg.status_code} {reg.json()}"
    response = client.post(
        "/auth/login",
        data={"username": email, "password": "secret123"},
    )
    return response.json()


def test_login_failure_identical(client):
    client.post(
        "/auth/register", json={"email": "x@test.com", "password": "secret123", "full_name": "X"}
    )
    wrong_pw = client.post("/auth/login", data={"username": "x@test.com", "password": "wrongwrong"})
    no_user = client.post(
        "/auth/login", data={"username": "ghost@test.com", "password": "wrongwrong"}
    )

    assert wrong_pw.status_code == 401
    assert no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()


def test_login_success(client):
    tokens = register_and_login(client)
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"


def test_me_requires_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


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
        "/auth/register", json={"email": "dev@test.com", "password": "123", "full_name": "Dev"}
    )
    assert response.status_code == 422


def test_me_with_token(client):
    tokens = register_and_login(client)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert response.json()["email"] == "user@test.com"


def test_me_rejects_refresh_token(client):
    tokens = register_and_login(client)
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )
    assert response.status_code == 401


def test_refresh_flow(client):
    tokens = register_and_login(client)
    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_token = refreshed.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me.status_code == 200


def test_refresh_garbage_token(client):
    garbage = client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert garbage.status_code == 401
