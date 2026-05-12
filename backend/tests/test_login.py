from app.constants import UserRole
from jwt import decode


def test_login_invalid_password(client):
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "wrong_password"}
    )

    assert response.status_code == 401
    assert response.json["msg"] == "Invalid username or password"


def test_login_success(app, client):
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "adminpass"}
    )

    assert response.status_code == 200
    assert "bearer" in response.json

    decoded = decode(
        response.json["bearer"],
        app.config["JWT_SECRET_KEY"],
        algorithms=[app.config.get("JWT_ALGORITHM")],
    )

    assert decoded["role"] == UserRole.ADMIN
