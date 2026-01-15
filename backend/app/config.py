import os
import dotenv

dotenv.load_dotenv()

class Config:
    # jwt
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-key-keep-it-secret'
    JWT_ALGORITHM = 'HS256'

    # admin
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'adminpass'

    # database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "sqlite+pysqlite:///app.db"

    # video uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or '/tmp/uploads'
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
