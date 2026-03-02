import uuid
import os

from flask import Blueprint, current_app, request, jsonify, send_from_directory

from app.utils import require_admin, require_authentication
from app.models import Experiment, User, Video
from app.extensions import db
from app.constants import UserRole

experiment_bp = Blueprint('experiment', __name__)


@experiment_bp.route('/', methods=['POST'])
@require_authentication
def create_experiment(_user_id, _role):
    """
    Create a new experiment (admin only).

    ---
    security:
        - Bearer: []
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - name
                    properties:
                        name:
                            type: string
    responses:
        201:
            description: Experiment created successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            id:
                                type: integer
                            name:
                                type: string
        400:
            description: Bad request
        401:
            description: Unauthorized
        403:
            description: Forbidden (admin only)
    """
    body = request.get_json()
    if not body or not body.get("name"):
        return jsonify({"msg": "name is required"}), 400

    if not (user := db.session.get(User, _user_id)):
        return jsonify({"msg": "User not found, bad auth state"}), 500
    
    experiment = Experiment(name=body["name"], users=[user])

    db.session.add(experiment)
    db.session.commit()

    return jsonify({"id": experiment.id, "name": experiment.name}), 201


@experiment_bp.route('/', methods=['GET'])
@require_authentication
@require_admin
def list_experiments(_user_id, _role):
    """
    List all experiments (admin only).

    ---
    security:
        - Bearer: []
    responses:
        200:
            description: List of experiments
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: object
                            properties:
                                id:
                                    type: integer
                                name:
                                    type: string
                                user_count:
                                    type: integer
                                video_count:
                                    type: integer
        401:
            description: Unauthorized
        403:
            description: Forbidden (admin only)
    """
    experiments = db.session.execute(db.select(Experiment)).scalars().all()

    return jsonify([
        {
            "id": e.id,
            "name": e.name,
            "user_count": len(e.users),
            "video_count": len(e.videos),
        }
        for e in experiments
    ]), 200


@experiment_bp.route('/me', methods=['GET'])
@require_authentication
def list_my_experiments(user_id, _role):
    """
    List all experiments the authenticated user is authorized to access.

    ---
    security:
        - Bearer: []
    responses:
        200:
            description: List of experiments for the current user
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: object
                            properties:
                                id:
                                    type: integer
                                name:
                                    type: string
                                video_count:
                                    type: integer
        401:
            description: Unauthorized
    """

    experiments = db.session.execute(
        db.select(Experiment).join(Experiment.users).where(User.id == user_id)
    ).scalars().all()

    return jsonify([
        {
            "id": e.id,
            "name": e.name,
            "video_count": len(e.videos),
        }
        for e in experiments
    ]), 200


@experiment_bp.route('/<int:experiment_id>', methods=['GET'])
@require_authentication
def get_experiment(user_id, role, experiment_id):
    """
    Get details of an experiment by ID. Accessible by admin or participant.

    ---
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          type: integer
          required: true
          description: The ID of the experiment
    responses:
        200:
            description: Experiment details
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            id:
                                type: integer
                            name:
                                type: string
                            users:
                                type: array
                                items:
                                    type: object
                                    properties:
                                        id:
                                            type: integer
                                        username:
                                            type: string
                            videos:
                                type: array
                                items:
                                    type: object
                                    properties:
                                        id:
                                            type: integer
                                        filename:
                                            type: string
                                        status:
                                            type: integer
        401:
            description: Unauthorized
        404:
            description: Experiment not found or not accessible
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        # non-existent looks the same as forbidden to avoid enumeration
        return jsonify({"msg": "Experiment not found"}), 404

    return jsonify({
        "id": experiment.id,
        "name": experiment.name,
        "users": [{"id": u.id, "username": u.username} for u in experiment.users],
        "videos": [
            {"id": v.id, "filename": v.filename, "status": v.status}
            for v in experiment.videos
        ],
    }), 200


@experiment_bp.route('/<int:experiment_id>', methods=['DELETE'])
@require_authentication
def delete_experiment(user_id, role, experiment_id):
    """
    Delete an experiment by ID (admin or participant). Associated videos are detached, not deleted.

    ---
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          type: integer
          required: true
          description: The ID of the experiment to delete
    responses:
        200:
            description: Experiment deleted successfully
        401:
            description: Unauthorized
        403:
            description: Forbidden (admin or participant)
        404:
            description: Experiment not found
    """

    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        # non-existent looks the same as forbidden to avoid enumeration
        return jsonify({"msg": "Experiment not found"}), 404

    db.session.delete(experiment)
    db.session.commit()

    return jsonify({"msg": "Experiment deleted"}), 200


@experiment_bp.route('/<int:experiment_id>/users', methods=['POST'])
@require_authentication
def add_user_to_experiment(_user_id, role, experiment_id):
    """
    Add a user to an experiment (admin or participant).

    ---
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          type: integer
          required: true
          description: The ID of the experiment
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    required:
                        - user_id
                    properties:
                        user_id:
                            type: integer
    responses:
        200:
            description: User added to experiment
        400:
            description: Bad request
        401:
            description: Unauthorized
        403:
            description: Forbidden (admin only)
        404:
            description: Experiment or user not found
        409:
            description: User already in experiment
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(_user_id):
        # non-existent looks the same as forbidden to avoid enumeration
        return jsonify({"msg": "Experiment not found"}), 404

    body = request.get_json()
    if not body or not body.get("user_id"):
        return jsonify({"msg": "user_id is required"}), 400

    user = db.session.get(User, body["user_id"])
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if user in experiment.users:
        return jsonify({"msg": "User already in experiment"}), 409

    experiment.users.append(user)
    db.session.commit()

    return jsonify({"msg": "User added to experiment"}), 200


@experiment_bp.route('/<int:experiment_id>/users/<int:target_user_id>', methods=['DELETE'])
@require_authentication
@require_admin
def remove_user_from_experiment(_user_id, _role, experiment_id, target_user_id):
    """
    Remove a user from an experiment (admin only).

    ---
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          type: integer
          required: true
          description: The ID of the experiment
        - name: target_user_id
          in: path
          type: integer
          required: true
          description: The ID of the user to remove
    responses:
        200:
            description: User removed from experiment
        401:
            description: Unauthorized
        403:
            description: Forbidden (admin only)
        404:
            description: Experiment or user not found
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    user = db.session.get(User, target_user_id)
    if not user or user not in experiment.users:
        return jsonify({"msg": "User not found in experiment"}), 404

    experiment.users.remove(user)
    db.session.commit()

    return jsonify({"msg": "User removed from experiment"}), 200


@experiment_bp.route('/<int:experiment_id>/videos', methods=['POST'])
@require_authentication
def upload_video_to_experiment(user_id, role, experiment_id):
    """
    Upload a video file and associate it with an experiment.
    The uploader must be a member of the experiment (or admin).

    ---
    security:
        - Bearer: []
    consumes:
        - multipart/form-data
    parameters:
        - name: experiment_id
          in: path
          type: integer
          required: true
          description: The ID of the experiment
        - name: file
          in: formData
          type: file
          required: true
          description: The video file to upload
    responses:
        201:
            description: Video uploaded successfully
        400:
            description: Bad request
        401:
            description: Unauthorized
        403:
            description: Not a member of the experiment
        404:
            description: Experiment not found
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        return jsonify({"msg": "Forbidden"}), 403

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

    if ext not in current_app.config['ALLOWED_VIDEO_EXTENSIONS']:
        return jsonify({"msg": "Invalid file type"}), 400

    real_filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], real_filename)

    new_video = Video(filename=file.filename, path=real_filename, experiment_id=experiment_id)

    db.session.add(new_video)
    db.session.flush()

    file.save(path)

    db.session.commit()

    return jsonify({"msg": "Video uploaded"}), 201


@experiment_bp.route('/<int:experiment_id>/videos/<int:video_id>', methods=['GET'])
@require_authentication
def download_video(user_id, role, experiment_id, video_id):
    """
    Download a video file from an experiment.

    ---
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          type: integer
          required: true
          description: The ID of the experiment
        - name: video_id
          in: path
          type: integer
          required: true
          description: The ID of the video to download
    responses:
        200:
            description: Video file returned successfully
            content:
                application/octet-stream:
                    schema:
                        type: string
                        format: binary
        401:
            description: Unauthorized
        404:
            description: Experiment or video not found
        500:
            description: Video file not found on server
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        return jsonify({"msg": "Experiment not found"}), 404

    video = db.session.get(Video, video_id)
    if not video or video.experiment_id != experiment_id:
        return jsonify({"msg": "Video not found in experiment"}), 404

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


@experiment_bp.route('/<int:experiment_id>/videos/<int:video_id>', methods=['DELETE'])
@require_authentication
def delete_video_from_experiment(user_id, role, experiment_id, video_id):
    """
    Delete a video from an experiment (file and DB record).

    ---
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          type: integer
          required: true
          description: The ID of the experiment
        - name: video_id
          in: path
          type: integer
          required: true
          description: The ID of the video to delete
    responses:
        200:
            description: Video deleted successfully
        401:
            description: Unauthorized
        403:
            description: Not a member of the experiment
        404:
            description: Experiment or video not found in experiment
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        return jsonify({"msg": "Experiment not found"}), 404

    video = db.session.get(Video, video_id)
    if not video or video.experiment_id != experiment_id:
        return jsonify({"msg": "Video not found in experiment"}), 404

    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], video.path))
    except FileNotFoundError:
        pass

    db.session.delete(video)
    db.session.commit()

    return jsonify({"msg": "Video deleted"}), 200
