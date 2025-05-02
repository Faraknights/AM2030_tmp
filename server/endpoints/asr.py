from flask import Blueprint, request, jsonify
import base64
import os
import uuid
import json

emotion_bp = Blueprint('emotion', __name__)

currentData = {
    "encoded_audio": "UklGRmw/AABXQ...+P/0UAYAA=",
    "transcription": " What?",
    "segment": "F",
    "ID": "Test_What",
}

@emotion_bp.route('/', methods=['POST'])
def update_current_data():
    global currentData

    data = request.get_json()
    currentData.update(data)

    return jsonify({"message": "Current data updated successfully"}), 200

@emotion_bp.route('/emotion', methods=['POST'])
def get_emotion():
    data = currentData

    try:
        print("start of the analyse")
        #emotion_result = analyze_emotion(data) 
        print("end of the analyse")
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in emotion recognition", "message": str(e)}), 500

    #return jsonify({
    #    "emotion": emotion_result
    #})
    return {}