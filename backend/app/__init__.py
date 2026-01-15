from flask import Flask
from flask_cors import CORS

from app.routes.auth import auth_bp
from app.routes.users import user_bp
from app.routes.videos import video_bp
from app.extensions import db
from app.config import Config

def setup_db(app: Flask):
    from app.models import User, UserRole

    with app.app_context():
        db.create_all()

        admin_username = "admin"
        stmt = db.select(User).where(User.username == admin_username)

        admin = db.session.execute(stmt).scalar_one_or_none()

        if not admin:

            pw = app.config.get('ADMIN_PASSWORD')

            if not pw:
                app.logger.fatal("ADMIN_PASSWORD is not set in configuration.")
                exit(1)

            new_admin = User(
                username=admin_username, 
                pw=pw,
                role=UserRole.ADMIN
            )

            db.session.add(new_admin)

            try:
                db.session.flush()
                db.session.commit()
                app.logger.info("Admin user created.")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Failed to create admin user: {e}")

                ...
        else:
            print("Admin user already exists.")
    

def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/*": {"origins": "*"}})

    app.config.from_object(Config)

    db.init_app(app)
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(video_bp, url_prefix='/api/video')

    return app