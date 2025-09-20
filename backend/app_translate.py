# from flask import Flask, request, jsonify
# import torch
# from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
# from IndicTransToolkit.processor import IndicProcessor

# app = Flask(__name__)

# # -----------------------------
# # LOAD MODEL ONCE
# # -----------------------------
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# src_lang, tgt_lang = "eng_Latn", "hin_Deva"
# model_name = "ai4bharat/indictrans2-en-indic-1B"

# tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
# model = AutoModelForSeq2SeqLM.from_pretrained(
#     model_name,
#     trust_remote_code=True,
#     dtype=torch.float32,          # CPU safe
#     attn_implementation="eager"   # important fix for CPU
# ).to(DEVICE)

# ip = IndicProcessor(inference=True)

# # -----------------------------
# # TRANSLATE ENDPOINT
# # -----------------------------
# @app.route("/translate", methods=["POST"])
# def translate():
#     data = request.get_json(force=True)
#     text = data.get("text")
    
#     if not text:
#         return jsonify({"error": "Missing 'text' in request"}), 400

#     try:
#         # Accept either single string or list of sentences
#         if isinstance(text, str):
#             input_sentences = [text]
#         elif isinstance(text, list):
#             input_sentences = text
#         else:
#             return jsonify({"error": "'text' must be string or list of strings"}), 400

#         # Preprocess with lang tags
#         batch = ip.preprocess_batch(input_sentences, src_lang=src_lang, tgt_lang=tgt_lang)

#         # Tokenize
#         inputs = tokenizer(
#             batch,
#             truncation=True,
#             padding="longest",
#             return_tensors="pt",
#             return_attention_mask=True,
#         ).to(DEVICE)

#         # Generate
#         with torch.no_grad():
#             generated_tokens = model.generate(
#                 **inputs,
#                 use_cache=False,   # fix NoneType bug
#                 min_length=0,
#                 max_length=256,
#                 num_beams=5,
#                 num_return_sequences=1,
#             )

#         # Decode
#         decoded = tokenizer.batch_decode(
#             generated_tokens,
#             skip_special_tokens=True,
#             clean_up_tokenization_spaces=True,
#         )

#         # Postprocess
#         translations = ip.postprocess_batch(decoded, lang=tgt_lang)

#         # Return JSON
#         return jsonify({"translations": translations})

#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": str(e)}), 500


# if __name__ == "__main__":
#     app.run(debug=True)

import torch
from flask import Flask, request, jsonify
from load_model import model, tokenizer, ip, DEVICE, SRC_LANG, TGT_LANG
from gtts import gTTS
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json(force=True)
    text = data.get("text")
    src_lang = data.get("src_lang", "eng_Latn")      # default English
    tgt_lang = data.get("tgt_lang", "hin_Deva")      # default Hindi

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400

    input_sentences = [text] if isinstance(text, str) else text

    try:
        # Preprocess
        batch = ip.preprocess_batch(input_sentences, src_lang=src_lang, tgt_lang=tgt_lang)

        # Tokenize
        inputs = tokenizer(batch, truncation=True, padding="longest", return_tensors="pt").to(DEVICE)

        # Generate
        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                use_cache=False,
                min_length=0,
                max_length=128,
                num_beams=5,
                num_return_sequences=1,
            )

        # Decode & postprocess
        decoded = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
        translations = ip.postprocess_batch(decoded, lang=tgt_lang)

        return jsonify({"translations": translations})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/translate_tts_google", methods=["POST"])
def translate_tts_google():
    """
    Converts the given text into speech using Google TTS.
    Expects JSON:
    {
        "text": "Your text here",
        "tgt_lang": "hi"  # 'hi' for Hindi, 'ta' for Tamil, 'te' for Telugu
    }
    Returns JSON:
    {
        "audio_file": "output.mp3",
        "translation": "Your text here"
    }
    """
    data = request.get_json(force=True)
    text = data.get("text")
    tgt_lang = data.get("tgt_lang", "hi")  # default Hindi

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400

    try:
        filename = "output.mp3"
        # gTTS uses 2-letter language codes
        tts = gTTS(text=text, lang=tgt_lang[:2])
        tts.save(filename)

        return jsonify({"audio_file": filename, "translation": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
