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


def test_register_admin_role(client, admin_token):
    response = client.post(
        "/api/user/",
        json={
            "username": "new_admin",
            "password": "secure_password",
            "role": UserRole.ADMIN,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    assert response.json["msg"] == "User created"

    response = client.get(
        "/api/user/2", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["username"] == "new_admin"
    assert response.json["role"] == UserRole.ADMIN


def test_register_user_role(client, admin_token):
    response = client.post(
        "/api/user/",
        json={
            "username": "new_user",
            "password": "secure_password",
            "role": UserRole.USER,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    assert response.json["msg"] == "User created"

    response = client.get(
        "/api/user/2", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["username"] == "new_user"
    assert response.json["role"] == UserRole.USER


def test_register_no_role_defaults_to_non_admin(client, admin_token):
    response = client.post(
        "/api/user/",
        json={"username": "new_user", "password": "secure_password"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    assert response.json["msg"] == "User created"

    response = client.get(
        "/api/user/2", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["username"] == "new_user"
    assert response.json["role"] != UserRole.ADMIN


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
        "/api/user/1/password", json={"new_password": "newpass", "old_password": "adminpass"}
    )
    assert response.status_code == 401


def test_change_password_missing_new_password(client, user_token):
    response = client.put(
        "/api/user/1/password",
        json={"old_password": "adminpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Password is required"


def test_change_password_own_correct_old_password(client, user_token):
    response = client.put(
        "/api/user/1/password",
        json={"new_password": "newpass", "old_password": "adminpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json["msg"] == "Password updated successfully"


def test_change_password_own_wrong_old_password(client, user_token):
    response = client.put(
        "/api/user/1/password",
        json={"new_password": "newpass", "old_password": "wrongpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Old password is incorrect"


def test_change_password_own_missing_old_password(client, user_token):
    response = client.put(
        "/api/user/1/password",
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
        "/api/user/2/password",
        json={"new_password": "newpass", "old_password": "otherpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
    assert response.json["msg"] == "Forbidden"


def test_change_own_password_admin_old_password_required(client, admin_token):
    response = client.put(
        "/api/user/1/password",
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
        "/api/user/2/password",
        json={"new_password": "newpass"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json["msg"] == "Password updated successfully"


def test_change_password_user_not_found(client, admin_token):
    response = client.put(
        "/api/user/999/password",
        json={"new_password": "newpass"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
    assert response.json["msg"] == "User not found"


def test_change_password_actually_updates(client, user_token):
    client.put(
        "/api/user/1/password",
        json={"new_password": "newpass", "old_password": "adminpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    # old password no longer works
    response = client.put(
        "/api/user/1/password",
        json={"new_password": "another", "old_password": "adminpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Old password is incorrect"
    # new password works
    response = client.put(
        "/api/user/1/password",
        json={"new_password": "another", "old_password": "newpass"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200


def test_delete_user_unauthenticated(client):
    response = client.delete("/api/user/1")
    assert response.status_code == 401
    assert response.json["msg"] == "Missing token"


def test_delete_user_non_admin(client, admin_token, user_token):
    # Admin creates a user to attempt to delete
    client.post(
        "/api/user/",
        json={"username": "victim", "password": "victimpass"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = client.delete(
        "/api/user/2",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
    assert response.json["msg"] == "Forbidden"


def test_delete_user_admin_success(client, admin_token):
    # Create a user to delete
    client.post(
        "/api/user/",
        json={"username": "to_delete", "password": "secure_password"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = client.delete(
        "/api/user/2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json["msg"] == "User deleted successfully"


def test_delete_user_not_found(client, admin_token):
    response = client.delete(
        "/api/user/999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
    assert response.json["msg"] == "User not found"


def test_delete_user_actually_removes(client, admin_token):
    # Create a user
    client.post(
        "/api/user/",
        json={"username": "to_delete", "password": "secure_password"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # User exists before deletion
    response = client.get(
        "/api/user/2", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

    # Delete the user
    response = client.delete(
        "/api/user/2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    # User no longer exists
    response = client.get(
        "/api/user/2", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    assert response.json["msg"] == "User not found"

    # Deleting again returns 404
    response = client.delete(
        "/api/user/2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
    assert response.json["msg"] == "User not found"
