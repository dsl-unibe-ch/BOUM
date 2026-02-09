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

    # gpustack
    SPEECH_UPSTREAM_URL = os.environ.get('SPEECH_UPSTREAM_URL') or 'https://gpustack.unibe.ch/v1/audio/transcriptions'
    GPUSTACK_API_TOKEN = os.environ.get('GPUSTACK_API_TOKEN') or 'upstream-api-key'
    COMPLETIONS_UPSTREAM_URL = os.environ.get('COMPLETIONS_API_TOKEN') or 'https://gpustack.unibe.ch/v1/chat/completions'
    SPEECH_MODEL = os.environ.get('SPEECH_MODEL') or 'faster-whisper-large-v3'
    COMPLETIONS_MODEL = os.environ.get('COMPLETIONS_MODEL') or 'gpt-oss-120b'