def test_register_unauth(client):
    response = client.post("/user/", json={
        "username": "new_user",
        "password": "secure_password"
    })
    
    assert response.status_code == 401
    assert response.json["msg"] == "Missing token"

def test_register_non_admin(client, user_token):
    response = client.post("/user/", json={
        "username": "new_user",
        "password": "secure_password"
    }, headers={
        "Authorization": f"Bearer {user_token}"
    })
    
    assert response.status_code == 403
    assert response.json["msg"] == "Forbidden"

def test_register_admin_success(client, admin_token):
    response = client.post("/user/", json={
        "username": "new_user",
        "password": "secure_password"
    }, headers={
        "Authorization": f"Bearer {admin_token}"
    })

    assert response.status_code == 201
    assert response.json["msg"] == "User created"
