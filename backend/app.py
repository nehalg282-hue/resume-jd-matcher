import re
import io
import nltk
from flask import Flask, request, jsonify
from flask_cors import CORS

nltk.data.path.append('/home/runner/nltk_data')
for resource, path in [
    ('tokenizers/punkt', 'punkt'),
    ('corpora/stopwords', 'stopwords'),
    ('tokenizers/punkt_tab', 'punkt_tab'),
    ('corpora/wordnet', 'wordnet'),
]:
    try:
        nltk.data.find(resource)
    except LookupError:
        nltk.download(path, quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STOP_WORDS = set(stopwords.words('english'))
STEMMER = PorterStemmer()

# Synonym map: every key normalises to its canonical form (the value).
# Keys include both directions so matching works both ways.
SYNONYM_MAP = {
    # JS ecosystem
    'reactjs': 'react',
    'react.js': 'react',
    'nodejs': 'node',
    'node.js': 'node',
    'expressjs': 'express',
    'express.js': 'express',
    'vuejs': 'vue',
    'vue.js': 'vue',
    'nextjs': 'next',
    'next.js': 'next',
    'nuxtjs': 'nuxt',
    'nuxt.js': 'nuxt',
    'js': 'javascript',
    'ts': 'typescript',
    # Cloud
    'aws': 'amazon web services',
    'amazon web services': 'aws',
    'gcp': 'google cloud platform',
    'google cloud': 'google cloud platform',
    # DevOps
    'ci/cd': 'continuous integration',
    'cicd': 'continuous integration',
    'continuous integration continuous deployment': 'continuous integration',
    'continuous integration/continuous deployment': 'continuous integration',
    # DB
    'postgresql': 'postgres',
    'postgres': 'postgres',
    'mongodb': 'mongo',
    'mongo db': 'mongo',
    # API
    'rest api': 'restful api',
    'restful api': 'restful api',
    'rest apis': 'restful api',
    'restful apis': 'restful api',
    # ML / Data
    'ml': 'machine learning',
    'dl': 'deep learning',
    'nlp': 'natural language processing',
    'cv': 'computer vision',
    'ai': 'artificial intelligence',
    # Misc
    'k8s': 'kubernetes',
    'tf': 'tensorflow',
    'pytorch': 'pytorch',
}

# Section header patterns used to detect resume sections
SECTION_PATTERNS = {
    'experience': re.compile(
        r'(work\s*experience|professional\s*experience|employment|experience)', re.I),
    'education': re.compile(
        r'(education|academic|qualification|degree|university|college)', re.I),
    'skills': re.compile(
        r'(skills|technical\s*skills|core\s*competencies|technologies|tech\s*stack)', re.I),
    'projects': re.compile(
        r'(projects?|personal\s*projects?|academic\s*projects?)', re.I),
    'certifications': re.compile(
        r'(certifications?|certificates?|licenses?|credentials?)', re.I),
    'summary': re.compile(
        r'(summary|objective|profile|about\s*me|career\s*objective)', re.I),
}

# Weighted importance of resume sections for the composite score
SECTION_WEIGHTS = {
    'skills': 0.50,
    'experience': 0.25,
    'projects': 0.15,
    'education': 0.05,
    'certifications': 0.05,
    'summary': 0.0,   # contributes to keyword pool but not scored separately
    'other': 0.0,
}

# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return ''.join(page.extract_text() or '' for page in reader.pages)
    except Exception:
        return ''


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return '\n'.join(p.text for p in doc.paragraphs)
    except Exception:
        return ''

# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

def normalise(text: str) -> str:
    """Lowercase, expand synonyms, strip punctuation, collapse whitespace."""
    text = text.lower()
    # Replace common separators with spaces
    text = re.sub(r'[\/\-\+\|]', ' ', text)
    # Apply multi-word synonyms first (longest first to avoid partial hits)
    for alias, canonical in sorted(SYNONYM_MAP.items(), key=lambda x: -len(x[0])):
        text = re.sub(r'\b' + re.escape(alias) + r'\b', canonical, text)
    # Remove remaining punctuation except alphanumeric + space
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenise(text: str) -> list:
    """Tokenise normalised text, remove stop-words and short tokens."""
    tokens = word_tokenize(text)
    return [t for t in tokens if t.isalpha() and t not in STOP_WORDS and len(t) > 2]


def stem(word: str) -> str:
    return STEMMER.stem(word)

# ---------------------------------------------------------------------------
# Resume section splitting
# ---------------------------------------------------------------------------

def split_into_sections(text: str) -> dict:
    """
    Split a resume into named sections.
    Handles two formats:
      1. Newline-based headings:  a short line that matches a section pattern
      2. Inline colon headings:   "Skills: React, Node.js ..."

    Returns a dict: section_name -> section_text.
    Everything before the first recognised heading goes into 'summary'.
    """
    # --- Pass 1: try to split on inline "Section: content" patterns ---
    inline_sections = {}
    for section, pattern in SECTION_PATTERNS.items():
        # Match "Skills: …" style inline headings
        inline_re = re.compile(
            r'(?:^|\n)' + pattern.pattern + r'\s*[:\-]\s*(.+?)(?=(?:\n[A-Z][^:]{0,40}[:\n])|$)',
            re.I | re.S
        )
        m = inline_re.search(text)
        if m:
            inline_sections[section] = m.group(m.lastindex)

    # --- Pass 2: standard newline-based heading split ---
    lines = text.split('\n')
    sections: dict = {}
    current = 'summary'
    buffer: list = []

    for line in lines:
        stripped = line.strip()
        matched_section = None
        for section, pattern in SECTION_PATTERNS.items():
            if pattern.search(stripped) and len(stripped) < 80:
                matched_section = section
                break
        if matched_section:
            if buffer:
                sections[current] = sections.get(current, '') + '\n' + '\n'.join(buffer)
            current = matched_section
            buffer = []
        else:
            buffer.append(line)

    if buffer:
        sections[current] = sections.get(current, '') + '\n' + '\n'.join(buffer)

    # Merge: inline sections fill in any gaps from newline-split
    for section, content in inline_sections.items():
        if section not in sections or not sections[section].strip():
            sections[section] = content

    # If still only 'summary' was found, do a best-effort keyword-based split
    detected = [s for s in sections if sections[s].strip() and s != 'summary']
    if not detected:
        # Treat the whole text as contributing to every section pool
        for section in ['skills', 'experience', 'projects', 'education', 'certifications']:
            sections[section] = text

    return sections

# ---------------------------------------------------------------------------
# Keyword extraction with synonym + stem awareness
# ---------------------------------------------------------------------------

def extract_keyword_set(text: str, top_n: int = 60) -> set:
    """
    Extract meaningful keyword tokens from text after normalisation.
    Returns a set of stemmed tokens for robust matching.
    """
    norm = normalise(text)
    tokens = tokenise(norm)
    # Build frequency map on stems, but keep original token for display
    freq = {}
    for t in tokens:
        s = stem(t)
        if s not in freq:
            freq[s] = {'count': 0, 'display': t}
        freq[s]['count'] += 1
    top = sorted(freq.items(), key=lambda x: -x[1]['count'])[:top_n]
    return {item[1]['display'] for item in top}


def extract_phrase_keywords(text: str) -> set:
    """
    Also extract 2-gram tech phrases (e.g. 'machine learning', 'restful api').
    """
    norm = normalise(text)
    tokens = word_tokenize(norm)
    tokens = [t for t in tokens if t.isalpha() and len(t) > 1]
    bigrams = {f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)
               if tokens[i] not in STOP_WORDS and tokens[i+1] not in STOP_WORDS}
    return bigrams


def get_all_keywords(text: str) -> set:
    return extract_keyword_set(text) | extract_phrase_keywords(text)

# ---------------------------------------------------------------------------
# Partial / semantic matching helpers
# ---------------------------------------------------------------------------

def tokens_match(tok_a: str, tok_b: str) -> bool:
    """True if tokens are identical or share the same stem."""
    if tok_a == tok_b:
        return True
    if stem(tok_a) == stem(tok_b):
        return True
    return False


def keyword_in_text(keyword: str, text_tokens: set, stemmed_tokens: set) -> bool:
    """
    Return True if `keyword` (possibly multi-word) appears in the token sets,
    using partial/stem matching.
    """
    kw_parts = keyword.split()
    if len(kw_parts) == 1:
        s = stem(kw_parts[0])
        return s in stemmed_tokens or kw_parts[0] in text_tokens
    # For multi-word: all words must individually match
    for part in kw_parts:
        if part in STOP_WORDS:
            continue
        if stem(part) not in stemmed_tokens and part not in text_tokens:
            return False
    return True

# ---------------------------------------------------------------------------
# Section-aware weighted scoring
# ---------------------------------------------------------------------------

def score_section(section_text: str, jd_stemmed: set, jd_tokens: set) -> float:
    """
    Return the fraction of JD keywords matched within this section's text.
    """
    if not section_text.strip():
        return 0.0
    sec_tokens = get_all_keywords(section_text)
    sec_stemmed = {stem(t.split()[0]) for t in sec_tokens}

    matched = sum(
        1 for kw in jd_tokens if keyword_in_text(kw, sec_tokens, sec_stemmed)
    )
    return matched / len(jd_tokens) if jd_tokens else 0.0


def compute_weighted_score(sections: dict, jd_stemmed: set, jd_tokens: set) -> dict:
    """
    Compute per-section match ratios and the weighted composite score.
    """
    section_scores = {}
    for section in ['skills', 'experience', 'projects', 'education', 'certifications', 'summary']:
        text = sections.get(section, '')
        section_scores[section] = round(score_section(text, jd_stemmed, jd_tokens) * 100, 1)

    weighted = 0.0
    for section, weight in SECTION_WEIGHTS.items():
        if weight > 0:
            weighted += (section_scores.get(section, 0) / 100) * weight

    return {
        'section_scores': section_scores,
        'weighted_score': round(weighted * 100, 1),
    }

# ---------------------------------------------------------------------------
# ATS scoring
# ---------------------------------------------------------------------------

def compute_ats_score(jd_keywords: set, resume_full_tokens: set,
                      resume_full_stemmed: set) -> dict:
    """
    ATS Score = (Matched JD Keywords / Total JD Keywords) × 100
    Returns matched, missing, and the score.
    """
    matched = []
    missing = []

    for kw in jd_keywords:
        if keyword_in_text(kw, resume_full_tokens, resume_full_stemmed):
            matched.append(kw)
        else:
            missing.append(kw)

    total = len(jd_keywords)
    ats_score = round(len(matched) / total * 100, 1) if total else 0.0

    return {
        'ats_score': ats_score,
        'matched_keywords': sorted(matched),
        'missing_keywords': sorted(missing),
        'total_jd_keywords': total,
        'total_matched': len(matched),
    }

# ---------------------------------------------------------------------------
# Master compute function
# ---------------------------------------------------------------------------

def compute_match(resume_text: str, jd_text: str) -> dict:
    # 1. Split resume into sections
    sections = split_into_sections(resume_text)

    # 2. Full resume token sets
    resume_full_tokens = get_all_keywords(resume_text)
    resume_full_stemmed = {stem(t.split()[0]) for t in resume_full_tokens}

    # 3. JD token sets
    jd_keywords = get_all_keywords(jd_text)
    jd_stemmed = {stem(t.split()[0]) for t in jd_keywords}

    # 4. ATS score (keyword coverage)
    ats = compute_ats_score(jd_keywords, resume_full_tokens, resume_full_stemmed)

    # 5. Weighted section score
    weighted = compute_weighted_score(sections, jd_stemmed, jd_keywords)

    # 6. Final blended score: 60% ATS keyword coverage + 40% weighted section
    final_score = round(
        0.60 * ats['ats_score'] + 0.40 * weighted['weighted_score'], 1
    )

    # 7. Keyword coverage percentage
    keyword_coverage = ats['ats_score']

    # 8. Experience match comes from the weighted section score for 'experience'
    experience_match = weighted['section_scores'].get('experience', 0.0)

    return {
        # Primary scores
        'match_percentage': final_score,
        'ats_score': ats['ats_score'],
        'keyword_coverage': keyword_coverage,
        'experience_match': experience_match,

        # Keyword results
        'matched_keywords': ats['matched_keywords'],
        'missing_keywords': ats['missing_keywords'],

        # Section breakdown
        'section_scores': weighted['section_scores'],
        'weighted_score': weighted['weighted_score'],

        # Debugging info
        'debug': {
            'total_jd_keywords': ats['total_jd_keywords'],
            'total_matched': ats['total_matched'],
            'exact_matched': ats['matched_keywords'],
            'exact_missing': ats['missing_keywords'],
            'sections_found': list(sections.keys()),
        },
    }

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/api/match', methods=['POST'])
def match():
    resume_text = ''
    jd_text = ''

    if 'resume_file' in request.files:
        f = request.files['resume_file']
        filename = f.filename.lower()
        file_bytes = f.read()
        if filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(file_bytes)
        elif filename.endswith('.docx'):
            resume_text = extract_text_from_docx(file_bytes)
        else:
            resume_text = file_bytes.decode('utf-8', errors='ignore')

    if not resume_text and 'resume_text' in request.form:
        resume_text = request.form['resume_text']

    if 'jd_text' in request.form:
        jd_text = request.form['jd_text']

    if not resume_text or not jd_text:
        return jsonify({'error': 'Both resume and job description are required.'}), 400

    result = compute_match(resume_text, jd_text)
    return jsonify(result)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=False)
