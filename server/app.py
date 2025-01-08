from flask import Flask
from endpoints.sentiment import sentiment_bp

app = Flask(__name__)

app.register_blueprint(sentiment_bp, url_prefix='/sentiment')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
