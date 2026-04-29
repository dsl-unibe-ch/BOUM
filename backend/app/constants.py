from enum import IntEnum

MAX_VIDEO_NAME_LEN = 200

class UserRole(IntEnum):
    ADMIN = 0
    USER = 1

class VideoStatus(IntEnum):
    PENDING = 0
    PROCESSING = 1
    PROCESSED = 2
    FAILED = 3

SWAGGER_TEMPLATE = {
    "swagger": None,
    "openapi": "3.0.0",
    "info": {
        "title": "BOUM Backend API",
        "version": "1.0.0",
    },
    "components": {
        "securitySchemes": {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "security": [{"Bearer": []}]
}  # type: ignore

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/api/docs/static/apispec.json',
            "rule_filter": lambda _: True,
            "model_filter": lambda _: True,
        }
    ],
    "static_url_path": "/api/docs/static/",
    "swagger_ui": True,
    "specs_route": "/api/docs/" 
}