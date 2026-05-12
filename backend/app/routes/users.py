from smtplib import OLDSTYLE_AUTH

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import User, UserRole
from app.schemas import UserFullDTO, UserSimpleDTO
from app.utils import create_jwt, require_admin, require_authentication, validate_body

user_bp = Blueprint("user", __name__)


@user_bp.route("/", methods=["POST"])
@require_authentication
@require_admin
@validate_body(UserSimpleDTO)
def add_user(_username: str, _role: int):
    """
    Add a new user to the system (admin only).
    ---
    tags:
        - Users
    security:
        - Bearer: []
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - username
                        - password
                    properties:
                        username:
                            type: string
                        password:
                            type: string
                        role:
                            type: integer
                            description: Optional user role (0 = admin, 1 = user). Defaults to regular user when omitted or unrecognized.
    responses:
        201:
            description: User created successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            msg:
                                type: string
                            username:
                                type: string
        400:
            description: Bad request
        401:
            description: Unauthorized
        403:
            description: Forbidden (admin only)
        409:
            description: Username already exists
    """

    user_dto = UserFullDTO(**request.get_json())

    existing_user = db.session.execute(
        db.select(User).filter_by(username=user_dto.username)
    ).scalar_one_or_none()

    if existing_user is not None:
        return jsonify({"msg": "Username already exists"}), 409

    role: None | UserRole
    match user_dto.role:
        case UserRole.ADMIN:
            role = UserRole.ADMIN
        case UserRole.USER:
            role = UserRole.USER
        case _:
            role = None

    if role is not None:
        new_user = User(user_dto.username, user_dto.password, role=role)
    else:
        new_user = User(user_dto.username, user_dto.password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created", "username": user_dto.username}), 201


@user_bp.route("/me", methods=["GET"])
@require_authentication
def get_my_info(user_id: int, _role: int):
    """
    Get the authenticated user's information.

    ---
    tags:
        - Users
    security:
        -  Bearer: []
    responses:
        200:
            description: User information returned successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            id:
                                type: integer
                            username:
                                type: string
                            role:
                                type: integer
        401:
            description: Unauthorized (authentication required)
    """

    user = db.session.execute(
        db.select(User).filter_by(id=user_id)
    ).scalar_one_or_none()

    if user is None:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({"id": user.id, "username": user.username, "role": user.role}), 200


@user_bp.route("/<int:target_user_id>", methods=["GET"])
@require_authentication
@require_admin
def get_user_info(_user_id: int, _role: int, target_user_id: int):
    """
    Get information about a specific user by ID (admin only).

    ---
    tags:
        - Users
    security:
        -  Bearer: []
    parameters:
        -   name: target_user_id
            in: path
            type: integer
            required: true
            description: The ID of the user to retrieve information for
    responses:
        200:
            description: User information returned successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            id:
                                type: integer
                            username:
                                type: string
                            role:
                                type: integer
        401:
            description: Unauthorized (authentication required)
        403:
            description: Forbidden (admin only endpoint)
        404:
            description: User not found
    """

    user = db.session.execute(
        db.select(User).filter_by(id=target_user_id)
    ).scalar_one_or_none()

    if user is None:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({"id": user.id, "username": user.username, "role": user.role}), 200


@user_bp.route("/", methods=["GET"])
@require_authentication
@require_admin
def list_users(_user_id: int, _role: int):
    """
    Get a list of all users in the system (admin only).

    ---
    tags:
        - Users
    security:
        -  Bearer: []
    responses:
        200:
            description: List of users returned successfully
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: object
                            properties:
                                id:
                                    type: integer
                                username:
                                    type: string
                                role:
                                    type: integer
        401:
            description: Unauthorized (authentication required)
        403:
            description: Forbidden (admin only endpoint)
    """

    users = db.session.execute(db.select(User)).scalars().all()

    user_list = [
        {"id": user.id, "username": user.username, "role": user.role} for user in users
    ]

    return jsonify(user_list), 200


@user_bp.route("/<int:target_user_id>", methods=["PUT"])
@require_authentication
def change_password(user_id: int, role: int, target_user_id: int):
    """
    Change the password of a user. Admins can change any user's password, while regular users can only change their own password.

    ---
    tags:
        - Users
    security:
        -  Bearer: []
    parameters:
        -   name: target_user_id
            in: path
            type: integer
            required: true
            description: The ID of the user whose password is to be changed
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - new_password
                        - old_password
                    properties:
                        new_password:
                            type: string
                        old_password:
                            type: string
    responses:
        200:
            description: Password updated successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            msg:
                                type: string
        400:
            description: Bad request (e.g., missing fields, incorrect old password)
        401:
            description: Unauthorized (authentication required)
        403:
            description: Forbidden (regular users can only change their own password)
        404:
            description: User not found
    """
    new_password = request.get_json().get("new_password")
    old_password = request.get_json().get("old_password")

    if not new_password:
        return jsonify({"msg": "Password is required"}), 400

    if role != UserRole.ADMIN and user_id != target_user_id:
        return jsonify({"msg": "Forbidden"}), 403

    user: User | None
    if not (
        user := db.session.execute(
            db.select(User).filter_by(id=target_user_id)
        ).scalar_one_or_none()
    ):
        return jsonify({"msg": "User not found"}), 404

    if (role == UserRole.ADMIN and user.id != user_id) or (
        old_password and user.verify_password(old_password)
    ):
        user.password = new_password
    else:
        return jsonify({"msg": "Old password is incorrect"}), 400

    db.session.commit()

    return jsonify({"msg": "Password updated successfully"}), 200
