import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit.processor import IndicProcessor

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "ai4bharat/indictrans2-en-indic-1B"
SRC_LANG, TGT_LANG = "eng_Latn", "hin_Deva"

# Load tokenizer + model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
    dtype=torch.float32,
    attn_implementation="eager"
).to(DEVICE)

# Processor
ip = IndicProcessor(inference=True)
