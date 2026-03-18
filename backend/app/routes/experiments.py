import uuid
import os

from flask import Blueprint, current_app, request, jsonify, send_from_directory

from datetime import datetime

from app.utils import require_admin, require_authentication
from app.models import Experiment, ExperimentMetadataDefaults, User, Video, VideoMetadata
from app.extensions import db
from app.constants import UserRole

experiment_bp = Blueprint('experiment', __name__)


@experiment_bp.route('/', methods=['POST'])
@require_authentication
def create_experiment(_user_id, _role):
    """
    Create a new experiment (all authenticated users).

    ---
    tags:
        - Experiments
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
    tags:
        - Experiments
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
    tags:
        - Experiments
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
    tags:
        - Experiments
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
                                        metadata:
                                            type: object
                                            nullable: true
                            metadata_defaults:
                                type: object
                                nullable: true
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
            {
                "id": v.id,
                "filename": v.filename,
                "status": v.status,
                "metadata": _serialize_video_metadata(v.video_metadata),
            }
            for v in experiment.videos
        ],
        "metadata_defaults": _serialize_metadata_defaults(experiment.metadata_defaults),
    }), 200


@experiment_bp.route('/<int:experiment_id>', methods=['DELETE'])
@require_authentication
def delete_experiment(user_id, role, experiment_id):
    """
    Delete an experiment by ID (admin or participant). Associated videos are detached, not deleted.

    ---
    tags:
        - Experiments
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
        404:
            description: Experiment not found or not accessible
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
    tags:
        - Experiments
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
    tags:
        - Experiments
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
    tags:
        - Experiments
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          schema:
              type: integer
          required: true
          description: The ID of the experiment
    requestBody:
        required: true
        content:
            multipart/form-data:
                schema:
                    type: object
                    properties:
                        file:
                            type: string
                            format: binary
                            description: The video file to upload
                    required:
                        - file
    responses:
        201:
            description: Video uploaded successfully
        400:
            description: Bad request
        401:
            description: Unauthorized
        404:
            description: Experiment not found or user not a member
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        return jsonify({"msg": "Experiment not found or user not a member"}), 404

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

    return jsonify({"id": new_video.id}), 201


@experiment_bp.route('/<int:experiment_id>/videos/<int:video_id>', methods=['GET'])
@require_authentication
def get_video(user_id, role, experiment_id, video_id):
    """
    Get video details and metadata.

    ---
    tags:
        - Experiments
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          schema:
              type: integer
          required: true
        - name: video_id
          in: path
          schema:
              type: integer
          required: true
    responses:
        200:
            description: Video details with metadata
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            id:
                                type: integer
                            filename:
                                type: string
                            status:
                                type: integer
                            download_url:
                                type: string
                            metadata:
                                type: object
                                nullable: true
                                properties:
                                    title:
                                        type: string
                                    species:
                                        type: string
                                    cultivar:
                                        type: string
                                    genotype:
                                        type: string
                                    plant_age:
                                        type: string
                                    plant_growth_stage:
                                        type: string
                                    growth_environment:
                                        type: string
                                    pot_volume:
                                        type: number
                                    substrate_type:
                                        type: string
                                    special_plant_treatments:
                                        type: string
                                    operator:
                                        type: string
                                    creation_date:
                                        type: string
                                        format: date-time
        401:
            description: Unauthorized
        404:
            description: Experiment or video not found
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        return jsonify({"msg": "Experiment not found"}), 404

    video = db.session.get(Video, video_id)
    if not video or video.experiment_id != experiment_id:
        return jsonify({"msg": "Video not found in experiment"}), 404

    return jsonify({
        "id": video.id,
        "filename": video.filename,
        "status": video.status,
        "download_url": f"/api/experiment/{experiment_id}/videos/{video_id}/download",
        "metadata": _serialize_video_metadata(video.video_metadata),
    }), 200


@experiment_bp.route('/<int:experiment_id>/videos/<int:video_id>/download', methods=['GET'])
@require_authentication
def download_video(user_id, role, experiment_id, video_id):
    """
    Download a video file from an experiment.

    ---
    tags:
        - Experiments
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          schema:
              type: integer
          required: true
        - name: video_id
          in: path
          schema:
              type: integer
          required: true
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
    tags:
        - Experiments
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
        404:
            description: Experiment or video not found
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


def _serialize_metadata_defaults(defaults):
    if defaults is None:
        return {}
    return {field: getattr(defaults, field) for field in ExperimentMetadataDefaults.metadata_fields()}


def _serialize_video_metadata(meta):
    if meta is None:
        return {}
    result = {}
    for field in VideoMetadata.metadata_fields():
        value = getattr(meta, field)
        if field == "creation_date" and value is not None:
            value = value.isoformat()
        result[field] = value
    return result


@experiment_bp.route('/<int:experiment_id>/metadata', methods=['GET'])
@require_authentication
def get_experiment_metadata_defaults(user_id, role, experiment_id):
    """
    Get default metadata for an experiment (admin or participant).

    ---
    tags:
        - Experiments
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          schema:
              type: integer
          required: true
    responses:
        200:
            description: Metadata defaults (null if not set)
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            metadata_defaults:
                                type: object
                                nullable: true
                                properties:
                                    species:
                                        type: string
                                    cultivar:
                                        type: string
                                    genotype:
                                        type: string
                                    plant_age:
                                        type: string
                                    plant_growth_stage:
                                        type: string
                                    growth_environment:
                                        type: string
                                    pot_volume:
                                        type: number
                                    substrate_type:
                                        type: string
                                    special_plant_treatments:
                                        type: string
                                    operator:
                                        type: string
        401:
            description: Unauthorized
        404:
            description: Experiment not found
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        return jsonify({"msg": "Experiment not found"}), 404

    return jsonify({"metadata_defaults": _serialize_metadata_defaults(experiment.metadata_defaults)}), 200


@experiment_bp.route('/<int:experiment_id>/metadata', methods=['POST'])
@require_authentication
def set_experiment_metadata_defaults(user_id, role, experiment_id):
    """
    Set default metadata for an experiment (admin or participant).

    ---
    tags:
        - Experiments
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          schema:
              type: integer
          required: true
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        species:
                            type: string
                        cultivar:
                            type: string
                        genotype:
                            type: string
                        plant_age:
                            type: string
                        plant_growth_stage:
                            type: string
                        growth_environment:
                            type: string
                        pot_volume:
                            type: number
                        substrate_type:
                            type: string
                        special_plant_treatments:
                            type: string
                        operator:
                            type: string
    responses:
        200:
            description: Metadata defaults set successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            msg:
                                type: string
                            metadata_defaults:
                                type: object
                                properties:
                                    species:
                                        type: string
                                    cultivar:
                                        type: string
                                    genotype:
                                        type: string
                                    plant_age:
                                        type: string
                                    plant_growth_stage:
                                        type: string
                                    growth_environment:
                                        type: string
                                    pot_volume:
                                        type: number
                                    substrate_type:
                                        type: string
                                    special_plant_treatments:
                                        type: string
                                    operator:
                                        type: string
        400:
            description: Bad request
        401:
            description: Unauthorized
        404:
            description: Experiment not found
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        return jsonify({"msg": "Experiment not found"}), 404

    body = request.get_json()
    if not body:
        return jsonify({"msg": "Request body is required"}), 400

    defaults = experiment.metadata_defaults
    if defaults is None:
        defaults = ExperimentMetadataDefaults(experiment_id=experiment_id)
        experiment.metadata_defaults = defaults

    for field in ExperimentMetadataDefaults.metadata_fields():
        value = body.get(field)
        if field == "pot_volume":
            setattr(defaults, field, float(value) if value is not None else None)
        else:
            setattr(defaults, field, value or None)

    db.session.commit()

    return jsonify({"msg": "Metadata defaults updated", "metadata_defaults": _serialize_metadata_defaults(defaults)}), 200


@experiment_bp.route('/<int:experiment_id>/videos/<int:video_id>/metadata', methods=['POST'])
@require_authentication
def set_video_metadata(user_id, role, experiment_id, video_id):
    """
    Set metadata for a video in an experiment (admin or participant).

    ---
    tags:
        - Experiments
    security:
        - Bearer: []
    parameters:
        - name: experiment_id
          in: path
          schema:
              type: integer
          required: true
        - name: video_id
          in: path
          schema:
              type: integer
          required: true
    requestBody:
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        title:
                            type: string
                        species:
                            type: string
                        cultivar:
                            type: string
                        genotype:
                            type: string
                        plant_age:
                            type: string
                        plant_growth_stage:
                            type: string
                        growth_environment:
                            type: string
                        pot_volume:
                            type: number
                        substrate_type:
                            type: string
                        special_plant_treatments:
                            type: string
                        operator:
                            type: string
                        creation_date:
                            type: string
                            format: date-time
    responses:
        200:
            description: Video metadata set successfully
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            msg:
                                type: string
                            metadata:
                                type: object
                                properties:
                                    title:
                                        type: string
                                    species:
                                        type: string
                                    cultivar:
                                        type: string
                                    genotype:
                                        type: string
                                    plant_age:
                                        type: string
                                    plant_growth_stage:
                                        type: string
                                    growth_environment:
                                        type: string
                                    pot_volume:
                                        type: number
                                    substrate_type:
                                        type: string
                                    special_plant_treatments:
                                        type: string
                                    operator:
                                        type: string
                                    creation_date:
                                        type: string
                                        format: date-time
        400:
            description: Bad request
        401:
            description: Unauthorized
        404:
            description: Experiment or video not found
    """
    if not (experiment := db.session.get(Experiment, experiment_id)):
        return jsonify({"msg": "Experiment not found"}), 404

    if role != UserRole.ADMIN and not experiment.is_user_participant(user_id):
        return jsonify({"msg": "Experiment not found"}), 404

    video = db.session.get(Video, video_id)
    if not video or video.experiment_id != experiment_id:
        return jsonify({"msg": "Video not found in experiment"}), 404

    body = request.get_json()
    if not body:
        return jsonify({"msg": "Request body is required"}), 400

    meta = video.video_metadata
    if meta is None:
        meta = VideoMetadata(video_id=video_id)
        video.video_metadata = meta

    for field in VideoMetadata.metadata_fields():
        value = body.get(field)
        if field == "pot_volume":
            setattr(meta, field, float(value) if value is not None else None)
        elif field == "creation_date":
            if value:
                try:
                    setattr(meta, field, datetime.fromisoformat(value))
                except (ValueError, TypeError):
                    return jsonify({"msg": "Invalid creation_date format, use ISO 8601"}), 400
            else:
                meta.creation_date = None
        else:
            setattr(meta, field, value or None)

    db.session.commit()

    return jsonify({"msg": "Video metadata updated", "metadata": _serialize_video_metadata(meta)}), 200
