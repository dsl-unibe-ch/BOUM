import io


# -- Experiment start_date --

def test_create_experiment_without_start_date(client, admin_token):
    response = client.post(
        "/api/experiment/",
        json={"name": "No Date Experiment"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    assert response.json["start_date"] is None


def test_create_experiment_with_start_date(client, admin_token):
    response = client.post(
        "/api/experiment/",
        json={"name": "Dated Experiment", "start_date": "2026-03-18T09:00:00"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    assert response.json["start_date"] == "2026-03-18T09:00:00"


def test_create_experiment_with_invalid_start_date(client, admin_token):
    response = client.post(
        "/api/experiment/",
        json={"name": "Bad Date", "start_date": "not-a-date"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


def test_get_experiment_returns_start_date(client, experiment, admin_token):
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "start_date" in response.json
    assert response.json["start_date"] is None


# -- Update experiment (PUT) --

def test_update_experiment_name(client, experiment, admin_token):
    response = client.put(
        f"/api/experiment/{experiment}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["name"] == "New Name"


def test_update_experiment_start_date(client, experiment, admin_token):
    response = client.put(
        f"/api/experiment/{experiment}",
        json={"start_date": "2026-01-15T08:00:00"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["start_date"] == "2026-01-15T08:00:00"


def test_update_experiment_both_fields(client, experiment, admin_token):
    response = client.put(
        f"/api/experiment/{experiment}",
        json={"name": "Updated", "start_date": "2026-06-01T12:00:00"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["name"] == "Updated"
    assert response.json["start_date"] == "2026-06-01T12:00:00"


def test_update_experiment_clear_start_date(client, experiment, admin_token):
    client.put(
        f"/api/experiment/{experiment}",
        json={"start_date": "2026-01-01T00:00:00"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.put(
        f"/api/experiment/{experiment}",
        json={"start_date": None},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["start_date"] is None


def test_update_experiment_invalid_start_date(client, experiment, admin_token):
    response = client.put(
        f"/api/experiment/{experiment}",
        json={"start_date": "bad"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


def test_update_experiment_unauthenticated(client, experiment):
    response = client.put(
        f"/api/experiment/{experiment}",
        json={"name": "Nope"}
    )
    assert response.status_code == 401


def test_update_experiment_non_member(client, experiment, non_member_user):
    _, token = non_member_user
    response = client.put(
        f"/api/experiment/{experiment}",
        json={"name": "Nope"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_update_experiment_not_found(client, admin_token):
    response = client.put(
        "/api/experiment/9999",
        json={"name": "Nope"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


# -- Experiment metadata defaults --

def test_set_experiment_metadata_unauthenticated(client, experiment):
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"species": "Arabidopsis"}
    )
    assert response.status_code == 401


def test_set_experiment_metadata_non_member(client, experiment, non_member_user):
    _, token = non_member_user
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"species": "Arabidopsis"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_set_experiment_metadata_not_found(client, admin_token):
    response = client.post(
        "/api/experiment/9999/metadata",
        json={"species": "Arabidopsis"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_set_experiment_metadata_empty_body(client, experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        headers={"Authorization": f"Bearer {admin_token}"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_set_experiment_metadata_admin(client, experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        json={
            "species": "Arabidopsis",
            "cultivar": "Col-0",
            "operator": "John",
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    defaults = response.json["metadata_defaults"]
    assert defaults["species"] == "Arabidopsis"
    assert defaults["cultivar"] == "Col-0"
    assert defaults["operator"] == "John"
    assert defaults["genotype"] is None


def test_set_experiment_metadata_member(client, experiment, member_user):
    _, token = member_user
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"species": "Tomato"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json["metadata_defaults"]["species"] == "Tomato"


def test_set_experiment_metadata_updates_existing(client, experiment, admin_token):
    client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"species": "Arabidopsis", "cultivar": "Col-0"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"species": "Tomato"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    defaults = response.json["metadata_defaults"]
    assert defaults["species"] == "Tomato"
    # cultivar was not sent, so it becomes None
    assert defaults["cultivar"] is None


def test_set_experiment_metadata_pot_volume_zero(client, experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"pot_volume": 0.0},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["metadata_defaults"]["pot_volume"] == 0.0


def test_set_experiment_metadata_pot_volume_null(client, experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"pot_volume": None},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["metadata_defaults"]["pot_volume"] is None


def test_set_experiment_metadata_empty_string_becomes_null(client, experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"species": ""},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["metadata_defaults"]["species"] is None


# -- GET experiment metadata defaults endpoint --

def test_get_experiment_metadata_endpoint_unauthenticated(client, experiment):
    response = client.get(f"/api/experiment/{experiment}/metadata")
    assert response.status_code == 401


def test_get_experiment_metadata_endpoint_non_member(client, experiment, non_member_user):
    _, token = non_member_user
    response = client.get(
        f"/api/experiment/{experiment}/metadata",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_get_experiment_metadata_endpoint_not_found(client, admin_token):
    response = client.get(
        "/api/experiment/9999/metadata",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_get_experiment_metadata_endpoint_null(client, experiment, admin_token):
    response = client.get(
        f"/api/experiment/{experiment}/metadata",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["metadata_defaults"] == {}


def test_get_experiment_metadata_endpoint_populated(client, experiment, admin_token):
    client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"species": "Arabidopsis", "pot_volume": 1.5},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.get(
        f"/api/experiment/{experiment}/metadata",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    defaults = response.json["metadata_defaults"]
    assert defaults["species"] == "Arabidopsis"
    assert defaults["pot_volume"] == 1.5


# -- GET experiment includes metadata_defaults --

def test_get_experiment_metadata_defaults_null(client, experiment, admin_token):
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["metadata_defaults"] == {}


def test_get_experiment_metadata_defaults_populated(client, experiment, admin_token):
    client.post(
        f"/api/experiment/{experiment}/metadata",
        json={"species": "Arabidopsis", "pot_volume": 1.5},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    defaults = response.json["metadata_defaults"]
    assert defaults["species"] == "Arabidopsis"
    assert defaults["pot_volume"] == 1.5


# -- Video metadata --

def test_set_video_metadata_unauthenticated(client, experiment, video_in_experiment):
    response = client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={"title": "My Video"}
    )
    assert response.status_code == 401


def test_set_video_metadata_non_member(client, experiment, video_in_experiment, non_member_user):
    _, token = non_member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={"title": "My Video"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_set_video_metadata_video_not_found(client, experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/videos/9999/metadata",
        json={"title": "My Video"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_set_video_metadata_experiment_not_found(client, admin_token, video_in_experiment):
    response = client.post(
        f"/api/experiment/9999/videos/{video_in_experiment}/metadata",
        json={"title": "My Video"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_set_video_metadata_empty_body(client, experiment, video_in_experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        headers={"Authorization": f"Bearer {admin_token}"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_set_video_metadata_success(client, experiment, video_in_experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={
            "title": "My Video",
            "species": "Arabidopsis",
            "cultivar": "Col-0",
            "pot_volume": 2.5,
            "creation_date": "2025-06-15T10:30:00",
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    meta = response.json["metadata"]
    assert meta["title"] == "My Video"
    assert meta["species"] == "Arabidopsis"
    assert meta["cultivar"] == "Col-0"
    assert meta["pot_volume"] == 2.5
    assert meta["creation_date"] == "2025-06-15T10:30:00"
    assert meta["genotype"] is None


def test_set_video_metadata_member(client, experiment, video_in_experiment, member_user):
    _, token = member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={"title": "Member's Video"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json["metadata"]["title"] == "Member's Video"


def test_set_video_metadata_invalid_date(client, experiment, video_in_experiment, admin_token):
    response = client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={"creation_date": "not-a-date"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400


def test_set_video_metadata_updates_existing(client, experiment, video_in_experiment, admin_token):
    client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={"title": "First Title", "species": "Arabidopsis"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={"title": "Second Title"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    meta = response.json["metadata"]
    assert meta["title"] == "Second Title"
    assert meta["species"] is None


# -- GET video returns JSON with metadata --

def test_get_video_returns_json(client, experiment, video_in_experiment, member_user):
    _, token = member_user
    response = client.get(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "id" in response.json
    assert "filename" in response.json
    assert "status" in response.json
    assert "download_url" in response.json
    assert "metadata" in response.json


def test_get_video_metadata_null_by_default(client, experiment, video_in_experiment, member_user):
    _, token = member_user
    response = client.get(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json["metadata"] == {}


def test_get_video_metadata_after_setting(client, experiment, video_in_experiment, admin_token):
    client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={"title": "Test", "species": "Tomato"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.get(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    meta = response.json["metadata"]
    assert meta["title"] == "Test"
    assert meta["species"] == "Tomato"


def test_get_video_unauthenticated(client, experiment, video_in_experiment):
    response = client.get(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}"
    )
    assert response.status_code == 401


def test_get_video_non_member(client, experiment, video_in_experiment, non_member_user):
    _, token = non_member_user
    response = client.get(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


# -- Upload does not auto-apply defaults --

def test_upload_no_auto_apply(client, experiment, member_user):
    _, token = member_user
    response = client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"content"), 'no_default.mkv')},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

    resp = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {token}"}
    )
    video = next(v for v in resp.json["videos"] if v["filename"] == "no_default.mkv")
    assert video["metadata"] == {}


# -- GET experiment shows video metadata --

def test_get_experiment_videos_include_metadata(client, experiment, video_in_experiment, admin_token):
    client.post(
        f"/api/experiment/{experiment}/videos/{video_in_experiment}/metadata",
        json={"title": "Labeled Video"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.get(
        f"/api/experiment/{experiment}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    video = next(v for v in response.json["videos"] if v["id"] == video_in_experiment)
    assert video["metadata"]["title"] == "Labeled Video"
