from flask import Blueprint, current_app, request, jsonify
from app.utils import require_authentication

import requests  # type: ignore
import json

audio_bp = Blueprint('audio', __name__)

PROMPT = """
System:
You translate natural language descriptions of plant growth into a JSON object
with the following format:

{
  "type": "object",
  "properties": {
    "grown": {
      "type": "boolean"
    },
    "healthy": {
      "type": "boolean"
    },
    "plant_name": {
      "type": "string"
    }
  },
  "required": [
    "grown",
    "healthy",
    "plant_name"
  ],
  "additionalProperties": false
}

Rules:
- ONLY output the json object, do not include any explanations or extra text.
- If information is missing or uncertain, make the field null.
"""

@audio_bp.route('/', methods=['POST'])
@require_authentication
def analyze_audio(_user_id, _role):
    """
    Upload an audio file and extract metadata.
    ---
    tags:
        - Audio
    security:
        - Bearer: []
    requestBody:
        content:
            multipart/form-data:
                schema:
                    type: object
                    properties:
                        file:
                            type: string
                            format: binary
                            description: The audio file to analyze
                    required:
                        - file
    responses:
        200:
            description: Analysis successful
            content:
                application/json:
                    schema:
                        type: object
        400:
            description: Bad request
        401:
            description: Unauthorized
        502:
            description: Upstream service error
    """

    headers = {
        'Authorization': f"Bearer {current_app.config["GPUSTACK_API_TOKEN"]}"
    }

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file_storage = request.files['file']

    files = {
        'file': (
            file_storage.filename,
            file_storage.stream,
            file_storage.content_type
        )
    }

    data = {
        'model': current_app.config["SPEECH_MODEL"],
        'language': 'auto'
    }

    try:
        speech_upstream_response = requests.post(
            current_app.config["SPEECH_UPSTREAM_URL"], 
            files=files,  # type: ignore 
            data=data, 
            headers=headers
        )

        transcription = speech_upstream_response.json()["text"]

    except (KeyError, json.JSONDecodeError) as _:
        return jsonify(
            {"error": "Invalid response from upstream speech service"}
        ), 502

    except requests.RequestException:
        return jsonify({"error": f"Upstream connection failed"}), 502

    payload = {
        "model": current_app.config["COMPLETIONS_MODEL"],
        "temperature": 0,
        "max_tokens": 40000,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "seed": None,
        "stop": None,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": transcription}
        ]
    }

    try:
        completion_upstream_response = requests.post(
            current_app.config["COMPLETIONS_UPSTREAM_URL"],
            json=payload,
            headers=headers
        )

        completion_upstream_response.raise_for_status()

        return json.loads(
            completion_upstream_response
                .json()["choices"][0]["message"]["content"]
        )

    except (KeyError, IndexError, json.JSONDecodeError):
        return jsonify(
            {"error": "Invalid response from upstream completion service"}
        ), 502

    except requests.RequestException:
        return jsonify({"error": f"Upstream completion failed"}), 502
