from flask import Flask, request, jsonify
from flask_cors import CORS
from deep_translator import GoogleTranslator
from gtts import gTTS
import uuid

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# -----------------------------
# Translate Endpoint (Google Translate)
# -----------------------------
@app.route("/translate", methods=["POST"])
def translate():
    """
    Request:
    {
      "text": "Hello world",
      "target_lang": "hi",
      "filename": "optional_file_name.txt"
    }
    Response:
    {
      "translated_text": "...",
      "audio_file": "optional_file_name.mp3"  # if used with TTS
    }
    """
    data = request.get_json(force=True)
    text = data.get("text")
    target_lang = data.get("target_lang", "en")
    filename = data.get("filename")  # optional

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400

    try:
        # Translate
        translated_text = GoogleTranslator(source="auto", target=target_lang).translate(text)

        response = {
            "original_text": text,
            "translated_text": translated_text,
            "target_lang": target_lang
        }

        # Optionally save translation to a file
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(translated_text)
            response["file_saved"] = filename

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Translate + TTS Endpoint
# -----------------------------
@app.route("/translate_tts_google", methods=["POST"])
def translate_tts_google():
    """
    Request:
    {
      "text": "Hello world",
      "target_lang": "hi",
      "filename": "optional_audio_name.mp3"
    }
    Response:
    {
      "translated_text": "...",
      "audio_file": "filename.mp3"
    }
    """
    data = request.get_json(force=True)
    text = data.get("text")
    target_lang = data.get("target_lang", "hi")
    filename = data.get("filename")

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400

    try:
        # Translate
        translated_text = GoogleTranslator(source="auto", target=target_lang).translate(text)

        # Generate audio filename if not provided
        if not filename:
            filename = f"tts_{target_lang}_{uuid.uuid4().hex[:8]}.mp3"

        # Text-to-Speech
        tts = gTTS(text=translated_text, lang=target_lang[:2])
        tts.save(filename)

        return jsonify({
            "original_text": text,
            "translated_text": translated_text,
            "target_lang": target_lang,
            "audio_file": filename
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
