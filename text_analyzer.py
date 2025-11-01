import re
import nltk
from typing import List
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64

# Optional transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

# ---------- Download NLTK resources ----------
nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("vader_lexicon", quiet=True)

STOPWORDS = set(stopwords.words("english"))

# ---------- Text Cleaning ----------
def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)  # remove extra spaces
    text = re.sub(r"http\S+|www\.\S+", "", text)  # remove URLs
    text = re.sub(r"[^A-Za-z0-9₹\s]", "", text)  # keep letters, numbers, ₹
    tokens = [t.lower() for t in word_tokenize(text)]
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens)

def tokenize(text: str) -> List[str]:
    return [t for t in word_tokenize(text.lower()) if t.isalpha() and t not in STOPWORDS]

# ---------- Sentiment Analysis ----------
sia = SentimentIntensityAnalyzer()

def analyze(text: str):
    scores = sia.polarity_scores(text)
    comp = scores["compound"]
    if comp >= 0.05:
        label = "positive"
    elif comp <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {
        "sentiment": label,
        "compound_score": comp,
        "positive": scores.get("pos", 0.0),
        "negative": scores.get("neg", 0.0),
        "neutral": scores.get("neu", 0.0),
    }

# ---------- Extractive Summarizer ----------
class Summarizer:
    def summarize(self, text: str, max_length: int = 120) -> str:
        if not text or not text.strip():
            return ""
        sentences = sent_tokenize(text)

        # If only one sentence → return keywords
        if len(sentences) == 1:
            tokens = [w.lower() for w in word_tokenize(text) if w.isalpha() and w.lower() not in STOPWORDS]
            return " ".join(tokens[:max_length])

        # Word frequencies
        words = [w.lower() for w in word_tokenize(text) if w.isalpha() and w.lower() not in STOPWORDS]
        freqs = Counter(words)

        s_scores = []
        for s in sentences:
            tokens = [w.lower() for w in word_tokenize(s) if w.isalpha()]
            score = sum(freqs.get(w, 0) for w in tokens if w not in STOPWORDS)
            s_scores.append((score, s))

        # Sort by score
        s_scores.sort(key=lambda x: x[0], reverse=True)

        # Pick top 2–3 sentences
        top_sentences = [s for _, s in s_scores[:3]]

        # Preserve original order
        ordered = [s for s in sentences if s in top_sentences]

        # Join complete sentences, but stop if we exceed max_length
        summary = []
        word_count = 0
        for s in ordered:
            w_len = len(s.split())
            if word_count + w_len > max_length:
                break
            summary.append(s)
            word_count += w_len

        return " ".join(summary)

# ---------- Word Cloud ----------
class WordCloudGenerator:
    def generate_image(self, text: str, width: int = 800, height: int = 400, max_words: int = 200, colormap: str = "viridis"):
        """Generate word cloud and return as PIL Image"""
        if not text or not text.strip():
            return None
        
        wc = WordCloud(width=width, height=height, background_color="white", max_words=max_words, colormap=colormap)
        image = wc.generate(text).to_image()
        return image

    def frequencies(self, text: str):
        tokens = [t for t in text.split() if len(t) > 1]
        freq = Counter(tokens)
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)

# ---------- Create objects ----------
extractive_summarizer = Summarizer()
wcg = WordCloudGenerator()

# Initialize abstractive summarizer (will be loaded on demand to improve startup time)
_abstractive_summarizer = None

def get_abstractive_summarizer():
    global _abstractive_summarizer
    if not TRANSFORMERS_AVAILABLE:
        raise ImportError("Transformers library is not available. Please install it to use abstractive summarization.")
    if _abstractive_summarizer is None:
        _abstractive_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return _abstractive_summarizer
