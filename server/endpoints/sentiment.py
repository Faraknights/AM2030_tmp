from flask import Blueprint, request, jsonify
from modules.sentiment_analysis import analyze_sentiment

sentiment_bp = Blueprint('sentiment', __name__)

@sentiment_bp.route('/', methods=['POST'])
def get_sentiment():
    data = request.get_json()
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
 
    sentiment = analyze_sentiment(text)
 
    return jsonify({"sentiment": sentiment, "confidence": 0.95})
