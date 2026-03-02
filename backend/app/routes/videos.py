from flask import Blueprint, jsonify

from app.utils import require_admin, require_authentication
from app.models import Video
from app.extensions import db

video_bp = Blueprint('video', __name__)


@video_bp.route('/', methods=['GET'])
@require_authentication
@require_admin
def list_videos(_user_id, _role):
    """
    List all videos in the system (admin only).

    ---
    security:
        -   Bearer: []
    responses:
        200:
            description: List of videos returned successfully
            content:
                application/json:
                    schema:
                        type: array
                        items:
                            type: object
                            properties:
                                id:
                                    type: integer
                                filename:
                                    type: string
                                experiment_id:
                                    type: integer
                                status:
                                    type: integer
        401:
            description: Unauthorized (authentication required)
        403:
            description: Forbidden (admin only)
    """

    videos = db.session.execute(db.select(Video)).scalars().all()

    video_list = [
        {
            "id": video.id,
            "filename": video.filename,
            "experiment_id": video.experiment_id,
            "status": video.status
        }
        for video in videos
    ]

    return jsonify(video_list), 200
