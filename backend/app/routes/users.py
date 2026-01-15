from flask import Blueprint, request, jsonify

from app.schemas import UserSimpleDTO
from app.models import User
from app.extensions import db
from app.utils import require_admin, require_authentication, validate_body, create_jwt

user_bp = Blueprint('user', __name__)

@user_bp.route('/', methods=['POST'])
@require_authentication
@require_admin
@validate_body(UserSimpleDTO)
def add_user(_username: str, _role: int):
    login_dto = UserSimpleDTO(**request.get_json())

    existing_user = db.session.execute(
        db.select(User).filter_by(username=login_dto.username)
    ).scalar_one_or_none()

    if existing_user is not None:
        return jsonify({"msg": "Username already exists"}), 409

    new_user = User(login_dto.username, login_dto.password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created", "username": login_dto.username}), 201

@user_bp.route('/me', methods=['GET'])
@require_authentication
def get_my_info(user_id: int, _role: int):
    user = db.session.execute(
        db.select(User).filter_by(id=user_id)
    ).scalar_one_or_none()

    if user is None:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "role": user.role
    }), 200

@user_bp.route('/<int:target_user_id>', methods=['GET'])
@require_authentication
@require_admin
def get_user_info(_user_id: int, _role: int, target_user_id: int):
    user = db.session.execute(
        db.select(User).filter_by(id=target_user_id)
    ).scalar_one_or_none()

    if user is None:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "role": user.role
    }), 200

@user_bp.route('/', methods=['GET'])
@require_authentication
@require_admin
def list_users(_user_id: int, _role: int):
    users = db.session.execute(db.select(User)).scalars().all()

    user_list = [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
        for user in users
    ]

    return jsonify(user_list), 200