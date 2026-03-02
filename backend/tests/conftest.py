import io
import os

import pytest
from app import create_app
from app.extensions import db
from sqlalchemy import StaticPool
from app.constants import UserRole
from app.config import Config

@pytest.fixture
def admin_password():
    return Config.ADMIN_PASSWORD

@pytest.fixture
def jwt_secret_key():
    return Config.JWT_SECRET_KEY

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {"poolclass": StaticPool}
    })

    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()

        from app.models import User
        admin = User(username="admin", pw="adminpass", role=UserRole.ADMIN)
        db.session.add(admin)
        db.session.commit()

        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client, app):
    from app.utils import create_jwt
    with app.app_context():
        return create_jwt(user_id=1, role=UserRole.ADMIN)

@pytest.fixture
def user_token(_client, app):
    from app.utils import create_jwt
    with app.app_context():
        return create_jwt(user_id=1, role=UserRole.USER)

@pytest.fixture
def experiment(client, admin_token):
    resp = client.post(
        "/api/experiment/",
        json={"name": "Test Experiment"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 201
    return resp.json["id"]

@pytest.fixture
def member_user(client, admin_token, experiment, app):
    from app.models import User
    from app.utils import create_jwt
    client.post(
        "/api/user/",
        json={"username": "member", "password": "memberpass"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    with app.app_context():
        user = db.session.execute(db.select(User).filter_by(username="member")).scalar_one()
        user_id = user.id
        token = create_jwt(user_id=user_id, role=UserRole.USER)
    client.post(
        f"/api/experiment/{experiment}/users",
        json={"user_id": user_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    return user_id, token

@pytest.fixture
def non_member_user(client, admin_token, app):
    from app.models import User
    from app.utils import create_jwt
    client.post(
        "/api/user/",
        json={"username": "nonmember", "password": "nonmemberpass"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    with app.app_context():
        user = db.session.execute(db.select(User).filter_by(username="nonmember")).scalar_one()
        user_id = user.id
        token = create_jwt(user_id=user_id, role=UserRole.USER)
    return user_id, token

@pytest.fixture
def video_in_experiment(client, member_user, experiment, app):
    from app.models import Video
    _, token = member_user
    client.post(
        f"/api/experiment/{experiment}/videos",
        data={'file': (io.BytesIO(b"fake video content"), 'test.mkv')},
        headers={"Authorization": f"Bearer {token}"}
    )
    with app.app_context():
        video = db.session.execute(
            db.select(Video).filter_by(experiment_id=experiment)
        ).scalars().first()
        assert video is not None
        return video.id
