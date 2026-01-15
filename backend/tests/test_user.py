from app.constants import UserRole

def test_register_unauth(client):
    response = client.post("/api/user/", json={
        "username": "new_user",
        "password": "secure_password"
    })

    assert response.status_code == 401
    assert response.json["msg"] == "Missing token"

def test_register_non_admin(client, user_token):
    response = client.post("/api/user/", json={
        "username": "new_user",
        "password": "secure_password"
    }, headers={
        "Authorization": f"Bearer {user_token}"
    })

    assert response.status_code == 403
    assert response.json["msg"] == "Forbidden"

def test_register_admin_success(client, admin_token):
    response = client.post("/api/user/", json={
        "username": "new_user",
        "password": "secure_password"
    }, headers={
        "Authorization": f"Bearer {admin_token}"
    })

    assert response.status_code == 201
    assert response.json["msg"] == "User created"

def test_register_existing_username(client, admin_token, app):
    client.post("/api/user/", json={
        "username": "existing_user",
        "password": "secure_password"
    }, headers={
        "Authorization": f"Bearer {admin_token}"
    })

    response = client.post("/api/user/", json={
        "username": "existing_user",
        "password": "another_password"
    }, headers={
        "Authorization": f"Bearer {admin_token}"
    })

    assert response.status_code == 409
    assert response.json["msg"] == "Username already exists"

def test_add_user_and_fetch_info(client, admin_token):
    # Register a new user
    response = client.post("/api/user/", json={
        "username": "test_user",
        "password": "test_password"
    }, headers={
        "Authorization": f"Bearer {admin_token}"
    })

    assert response.status_code == 201

    response = client.get("/api/user/2", headers={
        "Authorization": f"Bearer {admin_token}"
    })

    assert response.status_code == 200
    assert response.json["username"] == "test_user"
    assert response.json["role"] == UserRole.USER
