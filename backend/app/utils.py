import jwt  # type: ignore
import datetime

from functools import wraps
from flask import current_app, request, jsonify
from pydantic import ValidationError
from functools import wraps
from typing import Protocol
from sqlalchemy import inspect as sa_inspect, Float, DateTime

from app.constants import UserRole


def create_jwt(user_id, role):
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }

    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config.get('JWT_ALGORITHM', 'HS256')
    )


def require_authentication(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"msg": "Missing token"}), 401

        token = auth_header.split(" ")[1]

        try:
            data = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config.get('JWT_ALGORITHM', 'HS256')]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"msg": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"msg": "Invalid token"}), 401

        return f(int(data["sub"]), data["role"], *args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(user_id, role, *args, **kwargs):
        if role != UserRole.ADMIN:
            return jsonify({"msg": "Forbidden"}), 403

        return f(user_id, role, *args, **kwargs)
    return decorated


def validate_body(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                ...
            except ValidationError as e:
                return jsonify(e.errors()), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator


class HasSettableFields(Protocol):
    def settable_fields(self) -> list[str]: ...


def update_from_dict(obj: HasSettableFields, updates: dict) -> None:
    """Update an object's metadata fields from a dictionary, with type validation."""
    mapper = sa_inspect(type(obj))
    value: str | float | datetime.datetime | None = None

    for field in obj.settable_fields():
        if field not in updates:
            setattr(obj, field, None)
            continue

        raw = updates[field]
        if raw is None or raw == "":
            setattr(obj, field, None)
            continue

        match mapper.columns[field].type:  # type: ignore
            case Float():
                try:
                    value = float(raw)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid value for {field}: must be a number.")
            case DateTime():
                try:
                    value = datetime.datetime.fromisoformat(raw)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid value for {field}: must be an ISO format datetime string.")
            case _:
                value = raw

        setattr(obj, field, value)
