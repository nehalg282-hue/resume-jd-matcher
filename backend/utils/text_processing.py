"""
text_processing.py
NLP utilities: normalisation, tokenisation, stemming, and token pool construction.
"""
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

from .constants import SYNONYM_MAP

nltk.data.path.append('/home/runner/nltk_data')
for _resource, _pkg in [
    ('tokenizers/punkt', 'punkt'),
    ('corpora/stopwords', 'stopwords'),
    ('tokenizers/punkt_tab', 'punkt_tab'),
]:
    try:
        nltk.data.find(_resource)
    except LookupError:
        nltk.download(_pkg, quiet=True)

STOP_WORDS: set = set(stopwords.words('english'))
_STEMMER = PorterStemmer()


def stem(word: str) -> str:
    """Return the Porter stem of a lowercase word."""
    return _STEMMER.stem(word.lower())


def normalise(text: str) -> str:
    """
    Prepare text for matching:
      1. Lowercase
      2. Replace separators (/, -, +, |) with spaces
      3. Expand synonyms / aliases to canonical forms
      4. Strip non-alphanumeric characters
      5. Collapse whitespace
    """
    text = text.lower()
    text = re.sub(r'[\/\-\+\|]', ' ', text)
    for alias, canonical in sorted(SYNONYM_MAP.items(), key=lambda x: -len(x[0])):
        text = re.sub(r'\b' + re.escape(alias) + r'\b', canonical, text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenise(text: str) -> list:
    """
    Tokenise normalised text and filter out stop-words and very short tokens.
    Returns a list of lowercase alpha strings (length > 2).
    """
    tokens = word_tokenize(text)
    return [t for t in tokens if t.isalpha() and t not in STOP_WORDS and len(t) > 2]


def extract_token_set(text: str) -> set:
    """Return the unique set of meaningful single tokens from text."""
    return set(tokenise(normalise(text)))


def extract_bigram_set(text: str) -> set:
    """Return 2-gram phrases (both tokens non-stop) from normalised text."""
    norm = normalise(text)
    tokens = [t for t in word_tokenize(norm) if t.isalpha() and len(t) > 1]
    return {
        f"{tokens[i]} {tokens[i + 1]}"
        for i in range(len(tokens) - 1)
        if tokens[i] not in STOP_WORDS and tokens[i + 1] not in STOP_WORDS
    }


def get_token_pool(text: str) -> set:
    """Combined pool of single tokens and 2-gram phrases from text."""
    return extract_token_set(text) | extract_bigram_set(text)
