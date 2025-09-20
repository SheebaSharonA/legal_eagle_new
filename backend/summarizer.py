import nltk
from nltk.tokenize import sent_tokenize
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sentence_transformers import SentenceTransformer, util
import re
import pdfplumber
from abstractive import generate_abstractive_summary

# Download tokenizer once
nltk.download('punkt')


# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    # Clean text
    text = text.replace("\n", " ")
    text = re.sub(r"●|\•|\-|▪", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


# TextRank top sentences
def textrank_top_sentences(text, top_k=10):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, top_k)
    return [str(sentence) for sentence in summary]


# BERT-based sentence scores
def bert_sentence_scores(sentences, model):
    embeddings = model.encode(sentences, convert_to_tensor=True)
    doc_embedding = embeddings.mean(dim=0)
    scores = [util.cos_sim(doc_embedding, emb)[0][0].item() for emb in embeddings]
    return scores


# Hybrid summarization
def hybrid_summary(text, top_k_textrank=10, top_n_final=7, model_name='all-MiniLM-L6-v2', alpha=0.6):
    sentences = sent_tokenize(text)
    tr_sentences = textrank_top_sentences(text, top_k=top_k_textrank)
    tr_scores = [top_k_textrank - i for i in range(len(tr_sentences))]
    tr_dict = dict(zip(tr_sentences, tr_scores))
    
    model = SentenceTransformer(model_name)
    bert_scores = bert_sentence_scores(sentences, model)
    bert_dict = dict(zip(sentences, bert_scores))
    
    combined_scores = {}
    for sent in sentences:
        tr_score = tr_dict.get(sent, 0)
        bert_score = bert_dict.get(sent, 0)
        combined_scores[sent] = alpha * tr_score + (1 - alpha) * bert_score
    
    ranked_sentences = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    return [s for s, score in ranked_sentences[:top_n_final]]


# Main function to be called from Flask
def summarize_pdf(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    hybrid_sentences = hybrid_summary(text)
    abstractive_summary = generate_abstractive_summary(hybrid_sentences)
    return abstractive_summary, text
