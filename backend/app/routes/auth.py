from flask import Blueprint, request, jsonify

from app.schemas import UserSimpleDTO
from app.models import User
from app.extensions import db
from app.utils import validate_body, create_jwt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
@validate_body(UserSimpleDTO)
def login():
    """
    Login endpoint to obtain a Bearer Token.
    ---
    tags:
        - Auth
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
    responses:
        200:
            description: Successful login
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            bearer:
                                type: string
        401:
            description: Invalid username or password
    """

    login_dto = UserSimpleDTO(**request.get_json())

    user = db.session.execute(
        db.select(User).filter_by(username=login_dto.username)
    ).scalar_one_or_none()

    if user is None or not user.verify_password(login_dto.password):
        return jsonify({"msg": "Invalid username or password"}), 401

    return jsonify({"bearer": create_jwt(user.id, user.role)}), 200
