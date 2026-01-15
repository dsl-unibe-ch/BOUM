import io

def test_upload_video_unauth(client):
    response = client.post("/api/video/", data={})
    
    assert response.status_code == 401
    assert response.json["msg"] == "Missing token"


def test_upload_txt_non_admin(client, user_token):
    response = client.post(
        "/api/video/",
        data = {
            'file': (io.BytesIO(b"this is some test content"), 'test_file.txt'),
        }, 
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )
    
    assert response.status_code == 400
    assert response.json["msg"] == "Invalid file type"


def test_upload_mkv_non_admin(client, user_token):
    response = client.post(
        "/api/video/",
        data = {
            'file': (io.BytesIO(b"this is some test content"), 'test_vid.mkv'),
        }, 
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    assert response.status_code == 201
    assert response.json["msg"] == "Video uploaded"

    response = client.get(
        "/api/video/me",
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["filename"] == "test_vid.mkv"
    assert response.json[0]["id"] == 1

    response = client.get(
        f"/api/video/{response.json[0]['id']}",
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    assert response.status_code == 200

    print(response)
