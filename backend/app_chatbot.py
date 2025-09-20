# backend/app.py
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize
import re
import numpy as np
from flask_cors import CORS
from flask_cors import CORS

# NLTK setup
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

app = Flask(__name__)
CORS(app)


# Load the model once
model = SentenceTransformer('all-MiniLM-L6-v2')

# Store processed documents in memory
DOCUMENT_STORE = {}

# ------------------ Utilities ------------------
def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)
    return text.strip()

def chunk_text(text: str, method='sentence'):
    cleaned = clean_text(text)
    sentences = sent_tokenize(cleaned)
    if method == 'sentence':
        return [s for s in sentences if len(s.split()) >= 5]
    # small/medium/large chunk options can be added here
    return [cleaned]

def generate_summary(text: str) -> str:
    """Simple placeholder for summary (can be replaced with actual summarization model)"""
    sentences = sent_tokenize(text)
    # naive summary: first 3 sentences
    return " ".join(sentences[:3])

# ------------------ Endpoints ------------------
@app.route("/process_pdf_chatbot", methods=["POST"])
def process_pdf():
    """Process PDF for summary (called from frontend summary feature)"""
    data = request.json
    text = data.get("text")
    if not text or not text.strip():
        return jsonify({"error": "No text provided"}), 400
    
    cleaned_text = clean_text(text)
    summary = generate_summary(cleaned_text)
    
    # Store in memory for chatbot queries
    doc_id = str(len(DOCUMENT_STORE) + 1)
    chunks = chunk_text(cleaned_text, method='sentence')
    embeddings = model.encode(chunks)
    
    DOCUMENT_STORE[doc_id] = {
        "text": cleaned_text,
        "chunks": chunks,
        "embeddings": embeddings
    }
    
    return jsonify({
        "doc_id": doc_id
    })

@app.route("/query", methods=["POST"])
def query():
    """Handle chatbot queries"""
    data = request.json
    doc_id = data.get("doc_id")
    query_text = data.get("query")
    
    if not doc_id or doc_id not in DOCUMENT_STORE:
        return jsonify({"error": "Document not found"}), 404
    if not query_text:
        return jsonify({"error": "Query is required"}), 400
    
    doc_data = DOCUMENT_STORE[doc_id]
    query_emb = model.encode([query_text])
    sims = cosine_similarity(query_emb, doc_data["embeddings"])[0]
    top_indices = sims.argsort()[-5:][::-1]  # top 5 chunks
    
    relevant_chunks = [doc_data["chunks"][i] for i in top_indices if sims[i] > 0.2]
    if not relevant_chunks:
        return jsonify({"answer": "No relevant information found in the document."})
    
    answer = " ".join(relevant_chunks)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True,port=5002)
