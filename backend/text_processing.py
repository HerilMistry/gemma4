import re
from nltk.tokenize import sent_tokenize
import nltk

nltk.download("punkt")

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return sent_tokenize(text)