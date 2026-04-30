from app.constants import UserRole


def test_register_unauth(client):
    response = client.post(
        "/api/user/", json={"username": "new_user", "password": "secure_password"}
    )

    assert response.status_code == 401
    assert response.json["msg"] == "Missing token"


def test_register_non_admin(client, user_token):
    response = client.post(
        "/api/user/",
        json={"username": "new_user", "password": "secure_password"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 403
    assert response.json["msg"] == "Forbidden"


def test_register_admin_success(client, admin_token):
    response = client.post(
        "/api/user/",
        json={"username": "new_user", "password": "secure_password"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    assert response.json["msg"] == "User created"


def test_register_existing_username(client, admin_token, app):
    client.post(
        "/api/user/",
        json={"username": "existing_user", "password": "secure_password"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = client.post(
        "/api/user/",
        json={"username": "existing_user", "password": "another_password"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 409
    assert response.json["msg"] == "Username already exists"


def test_add_user_and_fetch_info(client, admin_token):
    # Register a new user
    response = client.post(
        "/api/user/",
        json={"username": "test_user", "password": "test_password"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201

    response = client.get(
        "/api/user/2", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    assert response.json["username"] == "test_user"
    assert response.json["role"] == UserRole.USER


def test_change_password_unauthenticated(client):
    response = client.put(
        "/api/user/1", json={"new_password": "newpass", "old_password": "adminpass"}
    )
    assert response.status_code == 401


def test_change_password_missing_new_password(client, user_token):
    response = client.put(
        "/api/user/1",
        json={"old_password": "adminpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Password is required"


def test_change_password_own_correct_old_password(client, user_token):
    response = client.put(
        "/api/user/1",
        json={"new_password": "newpass", "old_password": "adminpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json["msg"] == "Password updated successfully"


def test_change_password_own_wrong_old_password(client, user_token):
    response = client.put(
        "/api/user/1",
        json={"new_password": "newpass", "old_password": "wrongpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Old password is incorrect"


def test_change_password_own_missing_old_password(client, user_token):
    response = client.put(
        "/api/user/1",
        json={"new_password": "newpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Old password is incorrect"


def test_change_password_other_user_forbidden(client, admin_token, user_token):
    client.post(
        "/api/user/",
        json={"username": "other_user", "password": "otherpass"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = client.put(
        "/api/user/2",
        json={"new_password": "newpass", "old_password": "otherpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
    assert response.json["msg"] == "Forbidden"


def test_change_own_password_admin_old_password_required(client, admin_token):
    response = client.put(
        "/api/user/1",
        json={"new_password": "newpass"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Old password is incorrect"


def test_change_password_admin_changes_other_user(client, admin_token):
    client.post(
        "/api/user/",
        json={"username": "other_user", "password": "otherpass"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = client.put(
        "/api/user/2",
        json={"new_password": "newpass"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json["msg"] == "Password updated successfully"


def test_change_password_user_not_found(client, admin_token):
    response = client.put(
        "/api/user/999",
        json={"new_password": "newpass"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
    assert response.json["msg"] == "User not found"


def test_change_password_actually_updates(client, user_token):
    client.put(
        "/api/user/1",
        json={"new_password": "newpass", "old_password": "adminpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    # old password no longer works
    response = client.put(
        "/api/user/1",
        json={"new_password": "another", "old_password": "adminpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Old password is incorrect"
    # new password works
    response = client.put(
        "/api/user/1",
        json={"new_password": "another", "old_password": "newpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
