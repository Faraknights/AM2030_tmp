import subprocess
from flask import Blueprint, request, jsonify
import base64
import os
import whisper
import tempfile
import requests
import torch
import time

emotion_bp = Blueprint('emotion', __name__)
intention_category_bp = Blueprint('intention_category', __name__)
intention_bp = Blueprint('intention', __name__)

device = "cuda" if torch.cuda.is_available() else "cpu"
whisp = whisper.load_model("turbo", device=device)

model_busy = False


def post_with_retries(url, payload, retries=3, delay=0.05):
    """Send POST request with retries."""
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise RuntimeError("Error connecting with Ollama") from e


@emotion_bp.route('/emotion', methods=['POST'])
def get_emotion():
    global model_busy

    if model_busy:
        return jsonify({"error": "Model is currently busy"}), 503

    data = request.get_json()
    transcription = data.get("transcription")
    if transcription is None:
        return jsonify({"error": "No transcription provided"}), 400

    model_busy = True
    try:
        url = "http://ollama:11434/api/generate"
        payload = {
            "model": "emotion",
            "prompt": f"\"{transcription}\"",
            "stream": False
        }
        try:
            result = post_with_retries(url, payload)
        except RuntimeError:
            return jsonify({"error": "Error connecting with Ollama"}), 502

        return jsonify({"result": result["response"]})

    finally:
        model_busy = False


@intention_category_bp.route('/intention_category', methods=['POST'])
def get_intention_category():
    global model_busy

    if model_busy:
        return jsonify({"error": "Model is currently busy"}), 503

    data = request.get_json()
    transcription = data.get("transcription")
    if transcription is None:
        return jsonify({"error": "No transcription provided"}), 400

    model_busy = True
    try:
        url = "http://ollama:11434/api/generate"
        payload = {
            "model": "category",
            "prompt": f"\"{transcription}\"",
            "stream": False
        }
        try:
            result = post_with_retries(url, payload)
        except RuntimeError:
            return jsonify({"error": "Error connecting with Ollama"}), 502

        return jsonify({"result": result["response"]})
    finally:
        model_busy = False


@intention_bp.route('/intention', methods=['POST'])
def get_intention():
    global model_busy

    if model_busy:
        return jsonify({"error": "Model is currently busy"}), 503

    data = request.get_json()
    category_code = data.get("category_code")
    transcription = data.get("transcription")
    if category_code is None:
        return jsonify({"error": "No category_code provided"}), 400

    model_busy = True
    try:
        url = "http://ollama:11434/api/generate"
        payload = {
            "model": category_code,
            "prompt": f"\"{transcription}\"",
            "stream": False
        }
        try:
            result = post_with_retries(url, payload)
        except RuntimeError:
            return jsonify({"error": "Error connecting with Ollama"}), 502

        return jsonify({"result": result["response"]})
    finally:
        model_busy = False


@emotion_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    tmp_file_path = None
    resampled_path = None

    try:
        data = request.get_json()

        if not data or "encoded_audio" not in data:
            return jsonify({"error": "Missing 'encoded_audio' field"}), 400

        audio_data = base64.b64decode(data["encoded_audio"])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_file_path = tmp_file.name

        # Resample the audio to 16kHz mono WAV
        resampled_path = tmp_file_path.replace(".wav", "_resampled.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", tmp_file_path,
            "-ar", "16000", "-ac", "1", "-f", "wav", resampled_path
        ], check=True)

        result = whisp.transcribe(resampled_path, patience=2, beam_size=5)
        transcription = result.get("text", "").strip()

        return jsonify({"transcription": transcription}), 200

    except Exception as e:
        return jsonify({
            "error": "Transcription failed",
            "message": str(e)
        }), 500

    finally:
        for path in [tmp_file_path, resampled_path]:
            if path and os.path.exists(path):
                os.remove(path)
