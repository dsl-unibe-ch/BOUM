from flask import Blueprint, current_app, request, jsonify
from app.utils import require_authentication

import requests  # type: ignore
import json

audio_bp = Blueprint('audio', __name__)

PROMPT = """
System:
You translate natural language descriptions of plant experiments into a JSON object
with the following format:

{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "A short descriptive title for the video"
    },
    "species": {
      "type": "string",
      "description": "Plant species name"
    },
    "cultivar": {
      "type": "string",
      "description": "Plant cultivar or variety"
    },
    "genotype": {
      "type": "string",
      "description": "Genotype identifier"
    },
    "plant_age": {
      "type": "string",
      "description": "Age of the plant (e.g. '14 days', '3 weeks')"
    },
    "plant_growth_stage": {
      "type": "string",
      "description": "Growth stage (e.g. 'seedling', 'vegetative', 'flowering')"
    },
    "growth_environment": {
      "type": "string",
      "description": "Where the plant is grown (e.g. 'greenhouse', 'growth chamber', 'field')"
    },
    "pot_volume": {
      "type": "number",
      "description": "Volume of the pot in liters"
    },
    "substrate_type": {
      "type": "string",
      "description": "Growing substrate (e.g. 'soil', 'perlite', 'rockwool')"
    },
    "special_plant_treatments": {
      "type": "string",
      "description": "Any special treatments applied to the plant"
    },
    "operator": {
      "type": "string",
      "description": "Name of the person conducting the experiment"
    }
  },
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
                        properties:
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
                            transcription:
                                type: string
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
        return jsonify({"msg": "No file provided"}), 400

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
            {"msg": "Invalid response from upstream speech service"}
        ), 502

    except requests.RequestException:
        return jsonify({"msg": f"Upstream connection failed"}), 502

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

        metadata = json.loads(
            completion_upstream_response
                .json()["choices"][0]["message"]["content"]
        )

        return jsonify({
            "metadata": metadata,
            "transcription": transcription,
        })

    except (KeyError, IndexError, json.JSONDecodeError):
        return jsonify(
            {"msg": "Invalid response from upstream completion service"}
        ), 502

    except requests.RequestException:
        return jsonify({"msg": f"Upstream completion failed"}), 502
