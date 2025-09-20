from flask import Flask, request, jsonify
from flask_cors import CORS
import os, tempfile
from summarizer import summarize_pdf
import otp_manager
import logging

import firebase_admin
from firebase_admin import credentials, firestore, auth


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


app = Flask(__name__)
CORS(app)  # <-- This enables CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




@app.route("/request_otp", methods=["POST"])
def request_otp():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email required"}), 400

    otp = otp_manager.generate_otp(email)
    otp_manager.send_otp_email(email, otp)
    return jsonify({"message": "OTP sent to your email"})

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")
    if not email or not otp:
        return jsonify({"error": "Email and OTP required"}), 400

    if otp_manager.verify_otp(email, otp):
        # TODO: Save document to Firestore here
        return jsonify({"message": "OTP verified. Document saved successfully!"})
    else:
        return jsonify({"error": "Invalid OTP"}), 400
    

@app.route("/save_document", methods=["POST"])
def save_document():
    data = request.json

    id_token = data.get("idToken")
    file_name = data.get("fileName", "unknown.pdf")
    summary = data.get("summary")
    full_text = data.get("fullText")

    if not id_token:
        return jsonify({"error": "Missing ID token"}), 400
    if not summary or not full_text:
        return jsonify({"error": "No document content to save"}), 400

    try:
        # Verify Firebase token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]

        # Save document in subcollection: users/{uid}/documents
        doc_ref = db.collection("users").document(uid).collection("documents").document()
        doc_ref.set({
            "fileName": file_name,
            "summary": summary,
            "fullText": full_text,
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"message": "Document saved successfully"})
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed to save document"}), 500




@app.route("/process_pdf", methods=["POST"])
def process_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    language = request.form.get("language", "english")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        pdf_path = tmp.name

    # Summarize PDF (default English)
    summary, text = summarize_pdf(pdf_path)
    os.remove(pdf_path)

    # Translate if needed
    if language != "english":
        lang_code_map = {
            "tamil": "tam_Taml",
            "hindi": "hin_Deva",
            "spanish": "spa_Latn",
            "french": "fra_Latn"
        }
        tgt_lang = lang_code_map.get(language.lower(), "eng_Latn")
        summary = translate_en_to_indic(summary, tgt_lang=tgt_lang)
        text = translate_en_to_indic(text, tgt_lang=tgt_lang)

    return jsonify({"summary": summary, "text": text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
