from flask import Flask, jsonify
from endpoints.asr import emotion_bp 
from flask_cors import CORS
import os
import json
import torch

CONFIG_PATH = 'server/config.json'
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

with open(CONFIG_PATH) as config_file:
    config_data = json.load(config_file)

app = Flask(__name__)
CORS(app)

app.register_blueprint(emotion_bp, url_prefix='/asr') 


@app.route("/gpu")
def check_gpu():
    available = torch.cuda.is_available()
    return jsonify({"gpu_available": available})

if __name__ == '__main__':
    app.run(
        host=config_data.get('HOST', '127.0.0.1'),
        port=config_data.get('PORT', 5000),
        debug=False
    )
