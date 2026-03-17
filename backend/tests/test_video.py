import io


def test_upload_video_unauth(client, experiment):
    response = client.post(f"/api/experiment/{experiment}/videos", data={})

    assert response.status_code == 401
    assert response.json["msg"] == "Missing token"


def test_upload_no_file(client, member_user, experiment):
    _, token = member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.json["msg"] == "No file part"


def test_upload_txt_rejected(client, member_user, experiment):
    _, token = member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"this is some test content"), 'test_file.txt')},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert response.json["msg"] == "Invalid file type"


def test_upload_non_member_forbidden(client, non_member_user, experiment):
    _, token = non_member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"content"), 'test.mkv')},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_upload_and_download(client, member_user, experiment):
    _, token = member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"this is some test content"), 'test_vid.mkv')},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    assert response.json["msg"] == "Video uploaded"

    # video should appear in experiment details
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json["videos"]) == 1
    assert response.json["videos"][0]["filename"] == "test_vid.mkv"
    video_id = response.json["videos"][0]["id"]

    # get video info (now returns JSON)
    response = client.get(
        f"/api/experiment/{experiment}/videos/{video_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json["filename"] == "test_vid.mkv"
    assert "download_url" in response.json

    # download the video file
    response = client.get(
        f"/api/experiment/{experiment}/videos/{video_id}/download",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
