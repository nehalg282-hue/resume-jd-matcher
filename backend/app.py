"""
app.py
Flask application entry point for the Resume–JD Matcher API.

All matching logic lives in backend/utils/:
  constants.py       – synonym map, skill clusters, section patterns & weights
  file_parser.py     – PDF / DOCX / TXT extraction
  text_processing.py – normalise, tokenise, stem, get_token_pool
  section_parser.py  – split resume into named sections
  skill_matcher.py   – find_cluster, transferable_score, cluster_coverage
  scoring.py         – compute_keyword_match, compute_section_scores, calibrate_score
  reasoning.py       – build_confidence_reasoning
"""
import nltk
from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure NLTK data is available before importing utils that depend on it
nltk.data.path.append('/home/runner/nltk_data')
for _resource, _pkg in [
    ('tokenizers/punkt', 'punkt'),
    ('corpora/stopwords', 'stopwords'),
    ('tokenizers/punkt_tab', 'punkt_tab'),
    ('corpora/wordnet', 'wordnet'),
]:
    try:
        nltk.data.find(_resource)
    except LookupError:
        nltk.download(_pkg, quiet=True)

from utils.file_parser import extract_text_from_pdf, extract_text_from_docx
from utils.text_processing import get_token_pool
from utils.section_parser import split_into_sections
from utils.skill_matcher import find_cluster, cluster_coverage
from utils.scoring import (
    compute_keyword_match,
    compute_section_scores,
    compute_weighted_score,
    calibrate_score,
)
from utils.reasoning import build_confidence_reasoning
from utils.constants import SECTION_WEIGHTS

app = Flask(__name__)
CORS(app)


def compute_match(resume_text: str, jd_text: str) -> dict:
    """
    Master matching pipeline.

    Steps:
      1  Split resume into sections
      2  Build token pools for resume and JD
      3  Identify JD skills
      4  Cluster coverage (transferable credit)
      5  Keyword-level ATS match (concave curve)
      6  Section scores
      7  Weighted section composite
      8  Cluster composite
      9  Blended raw score  (30% kw + 30% sections + 40% clusters)
      10 Calibrate to recruiter scale
      11 Build confidence reasoning
    """
    sections = split_into_sections(resume_text)

    resume_pool = get_token_pool(resume_text)
    jd_pool = get_token_pool(jd_text)

    jd_skills = {t for t in jd_pool if find_cluster(t) is not None or len(t) > 3}

    cluster_results = cluster_coverage(resume_pool, jd_pool)
    keyword_result = compute_keyword_match(jd_pool, resume_pool)
    section_scores = compute_section_scores(sections, jd_pool, jd_skills)
    weighted_score = compute_weighted_score(section_scores)

    cluster_score = (
        sum(c['coverage'] for c in cluster_results.values()) / len(cluster_results)
        if cluster_results else 0.0
    )

    kw_coverage = keyword_result['coverage']
    raw_blended = 0.30 * kw_coverage + 0.30 * weighted_score + 0.40 * cluster_score
    final_score = calibrate_score(raw_blended)

    reasoning = build_confidence_reasoning(
        cluster_results, section_scores, keyword_result, sections
    )

    return {
        'match_percentage': final_score,
        'ats_score': round(kw_coverage, 1),
        'keyword_coverage': round(kw_coverage, 1),
        'experience_match': section_scores.get('experience', 0),
        'projects_match': section_scores.get('projects', 0),
        'weighted_score': weighted_score,
        'cluster_score': round(cluster_score, 1),

        'matched_keywords': keyword_result['matched_exact'],
        'partial_keywords': keyword_result['matched_partial'],
        'missing_keywords': keyword_result['missing'],

        'section_scores': section_scores,
        'cluster_results': cluster_results,
        'reasoning': reasoning,

        'debug': {
            'total_jd_keywords': keyword_result['total_jd_keywords'],
            'total_matched': len(keyword_result['matched_exact']),
            'partial_matched': len(keyword_result['matched_partial']),
            'effective_matched': keyword_result['effective_matched'],
            'sections_found': list(sections.keys()),
            'raw_blended': round(raw_blended, 1),
        },
    }


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

    return jsonify(compute_match(resume_text, jd_text))


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=False)
