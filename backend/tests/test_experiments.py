import io


# Create experiment
def test_create_experiment_unauthenticated(client):
    response = client.post("/api/experiment", json={"name": "X"})
    assert response.status_code == 401


def test_create_experiment_non_admin(client, non_member_user):
    _, token = non_member_user
    response = client.post(
        "/api/experiment",
        json={"name": "X"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201


def test_create_experiment_missing_name(client, admin_token):
    response = client.post(
        "/api/experiment",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


def test_create_experiment_success(client, admin_token):
    response = client.post(
        "/api/experiment",
        json={"name": "My Experiment"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    assert response.json["name"] == "My Experiment"
    assert "id" in response.json


# List experiments
def test_list_experiments_unauthenticated(client):
    response = client.get("/api/experiment")
    assert response.status_code == 401


def test_list_experiments_non_admin(client, non_member_user):
    _, token = non_member_user
    response = client.get(
        "/api/experiment",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_list_experiments_admin(client, admin_token, experiment):
    response = client.get(
        "/api/experiment",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["id"] == experiment


# Get experiment
def test_get_experiment_unauthenticated(client, experiment):
    response = client.get(f"/api/experiment/{experiment}")
    assert response.status_code == 401


def test_get_experiment_not_found(client, admin_token):
    response = client.get(
        "/api/experiment/9999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_get_experiment_as_non_member(client, experiment, non_member_user):
    _, token = non_member_user
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    # looks the same as not-found to prevent enumeration
    assert response.status_code == 404


def test_get_experiment_as_member(client, experiment, member_user):
    _, token = member_user
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json["id"] == experiment
    assert "users" in response.json
    assert "videos" in response.json


def test_get_experiment_as_admin(client, experiment, admin_token):
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["id"] == experiment


def test_get_experiment_shows_member(client, experiment, member_user, admin_token):
    member_id, _ = member_user
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    member_ids = [u["id"] for u in response.json["users"]]
    assert member_id in member_ids


# Delete experiment
def test_delete_experiment_unauthenticated(client, experiment):
    response = client.delete(f"/api/experiment/{experiment}")
    assert response.status_code == 401


def test_delete_experiment_non_admin(client, experiment, non_member_user):
    _, token = non_member_user
    response = client.delete(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_delete_experiment_success(client, experiment, admin_token):
    response = client.delete(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


# Add / remove users
def test_add_user_unauthenticated(client, experiment, non_member_user):
    user_id, _ = non_member_user
    response = client.post(
        f"/api/experiment/{experiment}/users",
        json={"user_id": user_id}
    )
    assert response.status_code == 401


def test_add_user_non_admin(client, experiment, non_member_user):
    user_id, token = non_member_user
    response = client.post(
        f"/api/experiment/{experiment}/users",
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_add_user_missing_body(client, experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/users",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


def test_add_user_success(client, experiment, admin_token, non_member_user):
    user_id, token = non_member_user
    response = client.post(
        f"/api/experiment/{experiment}/users",
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

    # user can now access the experiment
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_add_user_already_member(client, experiment, admin_token, member_user):
    member_id, _ = member_user
    response = client.post(
        f"/api/experiment/{experiment}/users",
        json={"user_id": member_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409


def test_remove_user_non_admin(client, experiment, member_user):
    member_id, token = member_user
    response = client.delete(
        f"/api/experiment/{experiment}/users/{member_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_remove_user_success(client, experiment, admin_token, member_user):
    member_id, token = member_user
    response = client.delete(
        f"/api/experiment/{experiment}/users/{member_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

    # user can no longer access the experiment
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


# List my experiments
def test_list_my_experiments_unauthenticated(client):
    response = client.get("/api/experiment/me")
    assert response.status_code == 401


def test_list_my_experiments_as_member(client, experiment, member_user):
    _, token = member_user
    response = client.get(
        "/api/experiment/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]["id"] == experiment


def test_list_my_experiments_as_non_member(client, experiment, non_member_user):
    _, token = non_member_user
    response = client.get(
        "/api/experiment/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json == []


# Upload / remove videos
def test_upload_video_unauthenticated(client, experiment):
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"content"), 'test.mkv')}
    )
    assert response.status_code == 401


def test_upload_video_non_member(client, experiment, non_member_user):
    _, token = non_member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"content"), 'test.mkv')},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_upload_video_any_member(client, experiment, admin_token):
    # A second member (not the original) can also upload a video
    client.post(
        "/api/user",
        json={"username": "member2", "password": "pass2"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    from app.models import User
    from app.utils import create_jwt
    from app.extensions import db
    from app.constants import UserRole
    with client.application.app_context():
        user2 = db.session.execute(db.select(User).filter_by(username="member2")).scalar_one()
        user2_id = user2.id
        token2 = create_jwt(user_id=user2_id, role=UserRole.USER)
    client.post(
        f"/api/experiment/{experiment}/users",
        json={"user_id": user2_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"content"), 'test.mkv')},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 201


def test_upload_video_member(client, experiment, member_user):
    _, token = member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"content"), 'test.mkv')},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201


def test_remove_video_unauthenticated(client, experiment, video_in_experiment):
    response = client.delete(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}"
    )
    assert response.status_code == 401


def test_remove_video_non_member(client, experiment, video_in_experiment, non_member_user):
    _, token = non_member_user
    response = client.delete(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_remove_video_member(client, experiment, member_user, video_in_experiment):
    _, token = member_user
    response = client.delete(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # video should no longer appear in the experiment
    resp = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    video_ids = [v["id"] for v in resp.json["videos"]]
    assert video_in_experiment not in video_ids


def test_remove_video_admin(client, experiment, admin_token, video_in_experiment):
    response = client.delete(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200


def test_get_experiment_shows_video(client, experiment, member_user, video_in_experiment):
    _, token = member_user
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    video_ids = [v["id"] for v in response.json["videos"]]
    assert video_in_experiment in video_ids
