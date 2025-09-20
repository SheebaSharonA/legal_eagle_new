# abstractive.py
from transformers import pipeline

# Load a working summarization model
abstractive_summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",     # <- stable summarization model
    tokenizer="facebook/bart-large-cnn",
    device=-1
)

def generate_abstractive_summary(extractive_sentences, max_len=150, min_len=40):
    """
    Takes a list of extractive sentences and returns a smooth abstractive summary.
    """
    text = " ".join(extractive_sentences)
    summary = abstractive_summarizer(
        text,
        max_length=max_len,
        min_length=min_len,
        do_sample=False
    )
    return summary[0]['summary_text']
