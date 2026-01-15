import uuid
import os

from flask import Blueprint, current_app, request, jsonify, send_from_directory

from app.utils import require_admin, require_authentication
from app.models import User, Video
from app.extensions import db
from app.constants import UserRole

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

    if not ext in current_app.config['ALLOWED_VIDEO_EXTENSIONS']:
        return jsonify({"msg": "Invalid file type"}), 400

    if file:
        real_filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], real_filename)

        if not (owner := db.session.get(User, user_id)):
            return jsonify({"msg": "User not found"}), 500

        new_video = Video(filename=file.filename, path=real_filename, owner=owner)

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


@video_bp.route('/<int:video_id>', methods=['GET'])
@require_authentication
def get_video(user_id, role, video_id):
    video = db.session.get(Video, video_id)

    if not video or not (video.owner_id == user_id or role == UserRole.ADMIN):
        # a non-existant video looks like a forbidden one, avoids enumerating IDs
        return jsonify({"msg": "Video not found"}), 404

    print(os.path.join(current_app.config['UPLOAD_FOLDER'], video.path))
    try:
        return send_from_directory(
            directory=current_app.config['UPLOAD_FOLDER'],
            path=video.path,
            as_attachment=True,
            download_name="".join(
                c if (c.isalnum() or c in ('.')) else '_' for c in video.filename
            )
        )
    except FileNotFoundError:
        return jsonify({"msg": "Video file not found on server"}), 500


@video_bp.route('/<int:video_id>', methods=['DELETE'])
@require_authentication
def delete_video(user_id, role, video_id):
    video = db.session.get(Video, video_id)

    if not video or (video.owner_id != user_id and role != UserRole.ADMIN):
        return jsonify({"msg": "Video not found"}), 404

    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], video.path))
    except FileNotFoundError:
        pass  # should this be an error?

    db.session.delete(video)
    db.session.commit()

    return jsonify({"msg": "Video deleted"}), 200

@video_bp.route('/', methods=['GET'])
@require_authentication
@require_admin
def list_videos(_user_id, _role):
    videos = db.session.execute(db.select(Video)).scalars().all()

    video_list = [
        {
            "id": video.id,
            "filename": video.filename,
            "owner_id": video.owner_id
        }
        for video in videos
    ]

    return jsonify(video_list), 200


@video_bp.route('/user/<int:owner_id>', methods=['GET'])
@require_authentication
def list_user_videos(user_id, role, owner_id):
    if user_id != owner_id and role != UserRole.ADMIN:
        return jsonify({"msg": "Forbidden"}), 403

    videos = db.session.execute(
        db.select(Video).filter_by(owner_id=owner_id)
    ).scalars().all()

    video_list = [
        {
            "id": video.id,
            "filename": video.filename,
        }
        for video in videos
    ]

    return jsonify(video_list), 200


@video_bp.route('/me', methods=['GET'])
@require_authentication
def list_my_videos(user_id, _role):
    videos = db.session.execute(
        db.select(Video).filter_by(owner_id=user_id)
    ).scalars().all()

    video_list = [
        {
            "id": video.id,
            "filename": video.filename,
        }
        for video in videos
    ]

    return jsonify(video_list), 200