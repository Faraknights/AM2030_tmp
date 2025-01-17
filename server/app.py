from flask import Flask, jsonify
from endpoints.sentiment import sentiment_bp
from endpoints.run import run_bp
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
import os
from config import Config

app = Flask(__name__)
CORS(app)

app.register_blueprint(sentiment_bp, url_prefix='/sentiment')
app.register_blueprint(run_bp, url_prefix='/run')

@app.route('/static/swagger.json')
def swagger_json():
    swagger_file_path = os.path.join(app.root_path, 'static/swagger.json')
    with open(swagger_file_path, 'r') as swagger_file:
        return swagger_file.read(), 200, {'Content-Type': 'application/json'}

SWAGGER_URL = '/swagger'
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    '/static/swagger.json',
    config={'app_name': "Flask Sentiment API"}
)

app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
