import pytest
from app import create_app
from app.extensions import db
from sqlalchemy import StaticPool
from app.constants import UserRole
from app.config import Config

from jwt import decode

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
        db.create_all()
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
def user_token(client, app):
    from app.utils import create_jwt
    with app.app_context():
        return create_jwt(user_id=1, role=UserRole.USER)