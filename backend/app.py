import os
import re
import io
import nltk
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nltk.data.path.append('/home/runner/nltk_data')
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(file_bytes):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return ""

def extract_text_from_docx(file_bytes):
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return ""

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_keywords(text, top_n=20):
    try:
        stop_words = set(stopwords.words('english'))
    except Exception:
        stop_words = set()
    tokens = word_tokenize(text.lower())
    keywords = [w for w in tokens if w.isalpha() and w not in stop_words and len(w) > 2]
    freq = {}
    for word in keywords:
        freq[word] = freq.get(word, 0) + 1
    sorted_kw = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [k for k, v in sorted_kw[:top_n]]

def compute_match(resume_text, jd_text):
    cleaned_resume = clean_text(resume_text)
    cleaned_jd = clean_text(jd_text)

    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    try:
        tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_jd])
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except Exception:
        score = 0.0

    resume_keywords = set(extract_keywords(resume_text))
    jd_keywords = set(extract_keywords(jd_text))

    matched = resume_keywords & jd_keywords
    missing = jd_keywords - resume_keywords

    match_percentage = round(score * 100, 1)

    return {
        "match_percentage": match_percentage,
        "matched_keywords": sorted(list(matched)),
        "missing_keywords": sorted(list(missing)),
        "resume_keywords": sorted(list(resume_keywords)),
        "jd_keywords": sorted(list(jd_keywords))
    }

@app.route('/api/match', methods=['POST'])
def match():
    resume_text = ""
    jd_text = ""

    if 'resume_file' in request.files:
        f = request.files['resume_file']
        filename = f.filename.lower()
        file_bytes = f.read()
        if filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(file_bytes)
        elif filename.endswith('.docx'):
            resume_text = extract_text_from_docx(file_bytes)
        elif filename.endswith('.txt'):
            resume_text = file_bytes.decode('utf-8', errors='ignore')
        else:
            resume_text = file_bytes.decode('utf-8', errors='ignore')

    if not resume_text and 'resume_text' in request.form:
        resume_text = request.form['resume_text']

    if 'jd_text' in request.form:
        jd_text = request.form['jd_text']

    if not resume_text or not jd_text:
        return jsonify({"error": "Both resume and job description are required."}), 400

    result = compute_match(resume_text, jd_text)
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=False)
