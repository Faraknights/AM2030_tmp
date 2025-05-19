import subprocess
from flask import Blueprint, request, jsonify
import base64
import os
import whisper
import tempfile

from modules.demo_aniti import run_classification 

emotion_bp = Blueprint('emotion', __name__)

whisp = whisper.load_model("base")

task_map = {
    "emotion": "systemMELD",
    "intention": "intention"
}

@emotion_bp.route('/emotion', methods=['POST'])
def get_emotion():
    data = request.get_json()
    transcription = data.get("transcription")
    task = data.get("task")

    if task not in task_map:
        return jsonify({"error": "Invalid task"}), 400

    result = run_classification(task, task_map[task], transcription)
    return {"result": result}

@emotion_bp.route('/cacheModel', methods=['POST'])
def get_cacheModel():
    data = request.get_json()
    task = data.get("task")

    if task not in task_map:
        return jsonify({"error": "Invalid task"}), 400

    run_classification(task, task_map[task], "t") #t for test
    return jsonify({"status": "ok"})

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

        result = whisp.transcribe(resampled_path, language='fr')
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
