import uuid
import os

from sqlalchemy import inspect
from flask import Blueprint, current_app, request, jsonify

from app.utils import require_authentication
from app.models import User, Video
from app.extensions import db

video_bp = Blueprint('video', __name__)

@video_bp.route('/', methods=['POST'])
@require_authentication
def upload_video(user_id, role):
    if "file" not in request.files:
        return jsonify({"msg": "No file part"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"msg": "No selected file"}), 400


    if len(file.filename) > Video.MAX_NAME_LEN:
        return jsonify(
            {"msg": f"Filename too long (max {Video.MAX_NAME_LEN} characters)"}
        ), 400

    ext = file.filename.split('.')[-1].lower()

    if file and ext in current_app.config['ALLOWED_VIDEO_EXTENSIONS']:
        path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.{ext}")

        if not (owner := db.session.get(User, user_id)):
            return jsonify({"msg": "User not found"}), 404

        new_video = Video(filename=file.filename, path=path, owner=owner)

        # The order matters here, first add and flush to get the ID assigned
        owner.videos.append(new_video)
        db.session.add(new_video)
        db.session.flush()

        # then save the file to disk
        file.save(path)

        # and commit the transaction, this only happens if the file save was
        # successful
        db.session.commit()

    return jsonify({"msg": "Video uploaded"}), 201
