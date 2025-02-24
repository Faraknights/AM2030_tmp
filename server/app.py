from flask import Flask, jsonify
from endpoints.sentiment import sentiment_bp
from endpoints.run import run_bp
from endpoints.asr import emotion_bp 
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
import os
import json

# Load configuration from file
CONFIG_PATH = 'server/config.json'
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

with open(CONFIG_PATH) as config_file:
    config_data = json.load(config_file)

app = Flask(__name__)
CORS(app)

# Register Blueprints
app.register_blueprint(sentiment_bp, url_prefix='/sentiment')
app.register_blueprint(run_bp, url_prefix='/run')
app.register_blueprint(emotion_bp, url_prefix='/asr')  # Updated registration

@app.route('/static/swagger.json')
def swagger_json():
    """Serve the Swagger JSON specification."""
    swagger_file_path = os.path.join(app.root_path, 'static/swagger.json')
    if not os.path.exists(swagger_file_path):
        return jsonify({"error": "Swagger JSON not found"}), 404

    with open(swagger_file_path, 'r') as swagger_file:
        return swagger_file.read(), 200, {'Content-Type': 'application/json'}

# Swagger UI setup
SWAGGER_URL = '/swagger'
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    '/static/swagger.json',
    config={'app_name': "Flask Sentiment API"}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(
        host=config_data.get('HOST', '127.0.0.1'),
        port=config_data.get('PORT', 5000),
        debug=config_data.get('DEBUG', False)
    )
