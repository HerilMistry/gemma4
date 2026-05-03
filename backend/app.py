from flask import Flask, request, jsonify
from flask_cors import CORS

from acoustic import extract_acoustic_features
from text_processing import preprocess_text
from llm import query_ollama

app = Flask(__name__)

CORS(app)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json

    text = data.get("text", "")
    typing_features = data.get("typing", {})
    audio_path = data.get("audio_path", None)

    audio_features = None
    if audio_path:
        audio_features = extract_acoustic_features(audio_path)

    processed_text = preprocess_text(text)

    context = f"""
    User text: {text}
    Typing: {typing_features}
    Audio: {audio_features}
    """

    response = query_ollama(context)

    return jsonify({
        "response": response,
        "audio_features": audio_features,
        "typing_features": typing_features
    })

if __name__ == "__main__":
    app.run(debug=True)