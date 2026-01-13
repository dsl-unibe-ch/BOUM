from flask import Flask

from app.routes.auth import auth_bp
from app.routes.users import user_bp
from app.routes.videos import video_bp
from app.extensions import db
from app.config import Config


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)
    
    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(video_bp, url_prefix='/video')

    with app.app_context():
        from app.models import User, UserRole
        db.create_all()

        admin_username = "admin"
        stmt = db.select(User).where(User.username == admin_username)
        admin = db.session.execute(stmt).scalar_one_or_none()

        if not admin:
            pw = app.config.get('ADMIN_PASSWORD')

            if not pw:
                raise AssertionError("ADMIN_PASSWORD is not set in configuration.")

            new_admin = User(
                username=admin_username, 
                pw=pw,
                role=UserRole.ADMIN
            )
            db.session.add(new_admin)
            db.session.commit()

            print("Admin created.")
        else:
            print("Admin user already exists.")

    return app