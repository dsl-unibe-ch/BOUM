from flask import Flask
from flask_cors import CORS
from sqlalchemy import event
from flasgger import Swagger  # type: ignore

from app.routes.auth import auth_bp
from app.routes.users import user_bp
from app.routes.videos import video_bp
from app.routes.audio import audio_bp
from app.routes.experiments import experiment_bp
from app.extensions import db
from app.config import Config
from app.constants import SWAGGER_CONFIG, SWAGGER_TEMPLATE

def setup_db(app: Flask):
    from app.models import User, UserRole, Video, Experiment

    with app.app_context():
        print(f"Registered tables: {db.metadata.tables.keys()}")
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

    swagger = Swagger(
        app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE, merge=False
    )

    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        # register an event listener for SQLite connects to set PRAGMAs
        # for Write-Ahead Logging and synchronous mode to get better
        # concurrency
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(video_bp, url_prefix='/api/video')
    app.register_blueprint(audio_bp, url_prefix='/api/audio')
    app.register_blueprint(experiment_bp, url_prefix='/api/experiment')

    return app
