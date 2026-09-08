import json
import os
import subprocess
import uuid
from io import BytesIO
from os.path import join as join_path
from typing import IO

import requests  # type: ignore
from app.utils import require_authentication
from flask import Blueprint, current_app, jsonify, request

audio_bp = Blueprint("audio", __name__)

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60 * 2

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


def transcribe(filename: str, file: IO[bytes] | BytesIO) -> str:
    """
    Transcribe the given audio file using the upstream speech-to-text service.

    :param file: A file-like object containing the audio data
    :return: The transcribed text
    :raises Exception: If the transcription fails or the response is invalid
    """
    headers = {"Authorization": f"Bearer {current_app.config['GPUSTACK_API_TOKEN']}"}

    files = {"file": (filename, file, "application/octet-stream")}

    data = {"model": current_app.config["SPEECH_MODEL"], "language": "auto"}

    try:
        response = requests.post(
            current_app.config["SPEECH_UPSTREAM_URL"],
            files=files,  # type: ignore
            data=data,
            headers=headers,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )

        response.raise_for_status()

        return response.json()["text"]

    except (KeyError, json.JSONDecodeError) as _:
        raise Exception("Invalid response from upstream speech service")

    except requests.RequestException as _:
        raise Exception("Upstream connection failed")


def remove_think_blocks(msg: str) -> str:
    marker_start = "<think>"
    marker_end = "</think>"

    def _gen(msg):
        read = [True]
        for (left, right) in ((msg[:i], msg[i:]) for i in range(len(msg))):
            if right.startswith(marker_start):
                read.append(False)
            if left.endswith(marker_end):
                _ = read.pop()
            if all(read):
                yield right[0]

    return "".join(_gen(msg))

def extract_metadata(transcription: str) -> dict:
    """
    Extract metadata from the given transcription using the upstream completion service.

    :param transcription: The transcribed text to analyze
    :return: A dictionary containing the extracted metadata
    :raises Exception: If the extraction fails or the response is invalid
    """

    headers = {"Authorization": f"Bearer {current_app.config['GPUSTACK_API_TOKEN']}"}

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
            {"role": "user", "content": transcription},
        ],
    }

    try:
        response = requests.post(
            current_app.config["COMPLETIONS_UPSTREAM_URL"],
            json=payload,
            headers=headers,
            timeout=(10, 300),
        )

        response.raise_for_status()

        message_content = response.json()["choices"][0]["message"]["content"]
        current_app.logger.info(
            "%s returned %s", current_app.config["COMPLETIONS_MODEL"], message_content
        )

        message_content = remove_think_blocks(message_content).strip()

        # LLMs do not reliably honor response_format={"type": "json_object"},
        # so we rely on the system prompt's "ONLY output the json object" rule
        # and parse the message content directly. May raise json.JSONDecodeError,
        # which is caught below.

        return json.loads(message_content)

    except (KeyError, IndexError, json.JSONDecodeError) as _:
        raise Exception("Invalid response from upstream completion service")

    except requests.RequestException as _:
        raise Exception("Upstream completion failed")


@audio_bp.route("", methods=["POST"])
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

    if "file" not in request.files:
        return jsonify({"msg": "No file provided"}), 400

    file_storage = request.files["file"]

    if not (filename := file_storage.filename):
        return jsonify({"msg": "Invalid filename"}), 400

    try:
        transcription = transcribe(filename, file_storage.stream)
    except Exception as e:
        return jsonify({"msg": f"Transcription error: {e}"}), 502

    try:
        extracted_metadata = extract_metadata(transcription)
    except Exception as e:
        return jsonify({"msg": f"Metadata extraction error: {e}"}), 502

    return jsonify(
        {"metadata": extracted_metadata, "transcription": transcription}
    ), 200


@audio_bp.route("/from-video", methods=["POST"])
@require_authentication
def analyze_audio_from_video(_user_id, _role):
    """
    Upload a video file, isolate audio and extract metadata.
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
                            description: The video file to analyze
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
    if "file" not in request.files:
        return jsonify({"msg": "No file part"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"msg": "No selected file"}), 400

    ext = file.filename.split(".")[-1].lower()

    if ext not in current_app.config["ALLOWED_VIDEO_EXTENSIONS"]:
        return jsonify({"msg": "Invalid file type"}), 400

    temp_file_name_base = f"tmp-{uuid.uuid4()}"
    temp_video_filename = f"{temp_file_name_base}.{ext}"

    upload_path = join_path(current_app.config["TEMP_VIDEO_DIR"], temp_video_filename)

    try:
        file.save(upload_path)
    except Exception as _:
        return jsonify({"msg": "Failed to save uploaded file"}), 500

    audio_file_name = f"{temp_file_name_base}.mp3"
    audio_dest_path = join_path(
        current_app.config["AUDIO_EXTRACTION_OUTPUT_DIR"], audio_file_name
    )
    cmd = (
        current_app.config["AUDIO_EXTRACTION_COMMAND_TEMPLATE"]
        .replace("%VIDEO%", str(upload_path))
        .replace(
            "%AUDIO%",
            str(audio_dest_path),
        )
    )

    try:
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            return jsonify({"msg": "Failed to extract audio from video"}), 500

        with open(audio_dest_path, "rb") as audio_file:
            audio_bytes = BytesIO(audio_file.read())

        try:
            transcription = transcribe(audio_file_name, audio_bytes)
        except Exception as e:
            return jsonify({"msg": f"Transcription error: {e}"}), 502

        try:
            extracted_metadata = extract_metadata(transcription)
        except Exception as e:
            return jsonify({"msg": f"Metadata extraction error: {e}"}), 502

        return jsonify(
            {"metadata": extracted_metadata, "transcription": transcription}
        ), 200
    finally:
        for path in (upload_path, audio_dest_path):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
