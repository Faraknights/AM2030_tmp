from flask import Flask, jsonify
from endpoints.asr import emotion_bp 
from flask_cors import CORS
import os
import json
import subprocess
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

# Call demo_aniti.py on startup
try:
    # Compute absolute path to demo_aniti.py
    script_path = os.path.join(os.path.dirname(__file__), 'modules', 'demo_aniti.py')
    result = subprocess.run(
        [
            "python3",
            script_path,
            "basic",
            "emotion",
            "systemMELD", 
            "ca m'enerve pourquoi tu me dis ca a chaque fois"
        ],
        capture_output=True,
        text=True,
        check=True
    )
    print("demo_aniti.py output:", result.stdout)
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
