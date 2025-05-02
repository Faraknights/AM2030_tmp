from flask import Flask, jsonify
from endpoints.asr import emotion_bp 
from flask_cors import CORS
import os
import json
import subprocess
import torch

from modules.demo_aniti import run_classification 

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

# Call demo_aniti.py on startup
try:
    result = run_classification("emotion", "systemMELD", "ca m'enerve pourquoi tu me dis ca a chaque fois")
except subprocess.CalledProcessError as e:
    print("Error calling demo_aniti.py:", e)
    print("Standard output:", e.stdout)
    print("Standard error:", e.stderr)

if __name__ == '__main__':
    app.run(
        host=config_data.get('HOST', '127.0.0.1'),
        port=config_data.get('PORT', 5000),
        debug=config_data.get('DEBUG', False)
    )
