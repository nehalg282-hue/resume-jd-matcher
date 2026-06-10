import re
import io
import math
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
# NLP primitives
# ---------------------------------------------------------------------------

STOP_WORDS = set(stopwords.words('english'))
STEMMER = PorterStemmer()

def stem(word: str) -> str:
    return STEMMER.stem(word.lower())

# ---------------------------------------------------------------------------
# Synonym / alias map  →  canonical token
# Both directions included so normalisation works from either side.
# ---------------------------------------------------------------------------
SYNONYM_MAP = {
    # JS framework aliases
    'react.js': 'react', 'reactjs': 'react',
    'next.js': 'nextjs', 'nextjs': 'nextjs',
    'vue.js': 'vue', 'vuejs': 'vue',
    'angular.js': 'angular', 'angularjs': 'angular',
    'node.js': 'node', 'nodejs': 'node',
    'express.js': 'express', 'expressjs': 'express',
    'nuxt.js': 'nuxt', 'nuxtjs': 'nuxt',
    # Language shorthands
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    # Cloud
    'aws': 'aws',
    'amazon web services': 'aws',
    'gcp': 'gcp',
    'google cloud platform': 'gcp',
    'google cloud': 'gcp',
    'azure': 'azure',
    'microsoft azure': 'azure',
    # DevOps
    'ci/cd': 'cicd', 'ci cd': 'cicd',
    'continuous integration': 'cicd',
    'continuous integration continuous deployment': 'cicd',
    'continuous integration/continuous deployment': 'cicd',
    # DB
    'postgresql': 'postgres', 'postgres': 'postgres',
    'mongodb': 'mongodb', 'mongo': 'mongodb', 'mongo db': 'mongodb',
    # API
    'rest api': 'rest', 'rest apis': 'rest',
    'restful api': 'rest', 'restful apis': 'rest',
    'graphql api': 'graphql',
    # Misc
    'k8s': 'kubernetes',
    'ml': 'machine learning',
    'ai': 'artificial intelligence',
    'nlp': 'natural language processing',
    'tf': 'tensorflow',
}

# ---------------------------------------------------------------------------
# Skill Clusters
# Each cluster: name → {members, transferable}
# transferable: other skills that earn partial credit when a member is missing
# ---------------------------------------------------------------------------
SKILL_CLUSTERS = {
    'Frontend': {
        'members': {'react', 'nextjs', 'angular', 'vue', 'svelte',
                    'javascript', 'typescript', 'html', 'css', 'tailwind',
                    'redux', 'webpack', 'vite'},
        'transferable': {
            # If JD wants react but resume has nextjs → high credit
            'react': [('nextjs', 0.9), ('angular', 0.5), ('vue', 0.5)],
            'nextjs': [('react', 0.85)],
            'angular': [('react', 0.5), ('vue', 0.5)],
            'vue': [('react', 0.5), ('angular', 0.5)],
            'javascript': [('typescript', 0.9)],
            'typescript': [('javascript', 0.8)],
        },
    },
    'Backend': {
        'members': {'node', 'express', 'django', 'flask', 'fastapi',
                    'spring', 'laravel', 'rails', 'rest', 'graphql',
                    'grpc', 'microservices', 'serverless'},
        'transferable': {
            'node': [('express', 0.85), ('django', 0.5), ('flask', 0.5)],
            'express': [('node', 0.85), ('fastapi', 0.6), ('flask', 0.6)],
            'django': [('flask', 0.7), ('fastapi', 0.7)],
            'flask': [('fastapi', 0.8), ('django', 0.7)],
            'rest': [('graphql', 0.7), ('grpc', 0.6)],
            'graphql': [('rest', 0.7)],
        },
    },
    'Databases': {
        'members': {'postgres', 'mysql', 'sqlite', 'mongodb', 'redis',
                    'elasticsearch', 'cassandra', 'dynamodb', 'oracle',
                    'mssql', 'mariadb'},
        'transferable': {
            'postgres': [('mysql', 0.8), ('mariadb', 0.8), ('oracle', 0.6), ('mssql', 0.6)],
            'mysql': [('postgres', 0.8), ('mariadb', 0.85), ('sqlite', 0.6)],
            'mongodb': [('dynamodb', 0.6), ('cassandra', 0.5), ('redis', 0.5)],
            'redis': [('elasticsearch', 0.5), ('mongodb', 0.4)],
            'dynamodb': [('mongodb', 0.6), ('cassandra', 0.55)],
        },
    },
    'Cloud & DevOps': {
        'members': {'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'cicd',
                    'jenkins', 'github actions', 'terraform', 'ansible',
                    'helm', 'linux', 'nginx', 'prometheus', 'grafana'},
        'transferable': {
            'aws': [('gcp', 0.7), ('azure', 0.7)],
            'gcp': [('aws', 0.7), ('azure', 0.7)],
            'azure': [('aws', 0.7), ('gcp', 0.7)],
            'docker': [('kubernetes', 0.7)],
            'kubernetes': [('docker', 0.7)],
            'cicd': [('jenkins', 0.75), ('github actions', 0.75)],
            'jenkins': [('cicd', 0.8), ('github actions', 0.7)],
        },
    },
    'Programming Languages': {
        'members': {'python', 'javascript', 'typescript', 'java', 'kotlin',
                    'scala', 'go', 'rust', 'ruby', 'php', 'cpp', 'csharp',
                    'swift', 'r'},
        'transferable': {
            'python': [('r', 0.4)],
            'javascript': [('typescript', 0.9)],
            'typescript': [('javascript', 0.85)],
            'java': [('kotlin', 0.85), ('scala', 0.6), ('csharp', 0.5)],
            'kotlin': [('java', 0.85), ('scala', 0.5)],
            'go': [('rust', 0.5), ('java', 0.4)],
        },
    },
    'Data & ML': {
        'members': {'machine learning', 'deep learning', 'tensorflow',
                    'pytorch', 'keras', 'scikit', 'pandas', 'numpy',
                    'spark', 'hadoop', 'tableau', 'powerbi', 'data analysis',
                    'data science', 'nlp', 'computer vision'},
        'transferable': {
            'tensorflow': [('pytorch', 0.85), ('keras', 0.8)],
            'pytorch': [('tensorflow', 0.85), ('keras', 0.75)],
            'machine learning': [('deep learning', 0.8), ('data science', 0.8)],
            'pandas': [('numpy', 0.7), ('spark', 0.6)],
        },
    },
    'Testing & Quality': {
        'members': {'jest', 'mocha', 'pytest', 'junit', 'selenium',
                    'cypress', 'playwright', 'testing', 'unit testing',
                    'integration testing', 'tdd', 'bdd'},
        'transferable': {
            'jest': [('mocha', 0.8), ('pytest', 0.5)],
            'cypress': [('playwright', 0.85), ('selenium', 0.7)],
            'pytest': [('junit', 0.7), ('jest', 0.5)],
            'tdd': [('bdd', 0.75), ('testing', 0.8)],
        },
    },
}

# Section detection patterns
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

# Updated weights: experience/projects matter more
SECTION_WEIGHTS = {
    'skills': 0.35,
    'experience': 0.35,
    'projects': 0.20,
    'education': 0.05,
    'certifications': 0.05,
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
    """Lowercase → synonym-expand → strip punctuation → collapse spaces."""
    text = text.lower()
    text = re.sub(r'[\/\-\+\|]', ' ', text)
    for alias, canonical in sorted(SYNONYM_MAP.items(), key=lambda x: -len(x[0])):
        text = re.sub(r'\b' + re.escape(alias) + r'\b', canonical, text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenise(text: str) -> list:
    tokens = word_tokenize(text)
    return [t for t in tokens if t.isalpha() and t not in STOP_WORDS and len(t) > 2]


def extract_token_set(text: str) -> set:
    """Return a set of unique normalised tokens from text."""
    norm = normalise(text)
    return set(tokenise(norm))


def extract_bigram_set(text: str) -> set:
    """Return 2-gram phrases after normalisation."""
    norm = normalise(text)
    tokens = [t for t in word_tokenize(norm) if t.isalpha() and len(t) > 1]
    return {
        f"{tokens[i]} {tokens[i+1]}"
        for i in range(len(tokens) - 1)
        if tokens[i] not in STOP_WORDS and tokens[i+1] not in STOP_WORDS
    }


def get_token_pool(text: str) -> set:
    """All single tokens + bigrams from text."""
    return extract_token_set(text) | extract_bigram_set(text)

# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------

def split_into_sections(text: str) -> dict:
    """Split resume into named sections; fall back to full text per section."""
    # Pass 1 – newline-based headings
    lines = text.split('\n')
    sections: dict = {}
    current = 'summary'
    buffer: list = []

    for line in lines:
        stripped = line.strip()
        matched = None
        for sec, pattern in SECTION_PATTERNS.items():
            if pattern.search(stripped) and len(stripped) < 80:
                matched = sec
                break
        if matched:
            if buffer:
                sections[current] = sections.get(current, '') + '\n' + '\n'.join(buffer)
            current = matched
            buffer = []
        else:
            buffer.append(line)
    if buffer:
        sections[current] = sections.get(current, '') + '\n' + '\n'.join(buffer)

    # Pass 2 – inline "Skills: …" patterns
    for sec, pattern in SECTION_PATTERNS.items():
        if sec not in sections or not sections[sec].strip():
            m = re.search(
                r'(?:^|\n)' + pattern.pattern + r'\s*[:\-]\s*(.+?)(?=\n[A-Z]|$)',
                text, re.I | re.S
            )
            if m:
                sections[sec] = m.group(m.lastindex)

    # Fallback – no sections detected → use full text for all
    detected = [s for s in sections if sections[s].strip() and s != 'summary']
    if not detected:
        for sec in ['skills', 'experience', 'projects', 'education', 'certifications']:
            sections[sec] = text

    return sections

# ---------------------------------------------------------------------------
# Semantic / transferable skill matching
# ---------------------------------------------------------------------------

def find_cluster(skill: str) -> str | None:
    """Return the cluster name for a skill, or None."""
    for cluster_name, cluster in SKILL_CLUSTERS.items():
        if skill in cluster['members']:
            return cluster_name
    return None


def transferable_score(wanted: str, resume_pool: set) -> float:
    """
    Return a [0, 1] score for `wanted` using transferable skill credit.
    1.0 = exact match, <1.0 = partial from related skill.
    """
    if wanted in resume_pool or any(stem(wanted) == stem(t) for t in resume_pool):
        return 1.0

    best = 0.0
    for cluster in SKILL_CLUSTERS.values():
        transfers = cluster['transferable'].get(wanted, [])
        for alt, credit in transfers:
            if alt in resume_pool or any(stem(alt) == stem(t) for t in resume_pool):
                best = max(best, credit)

    return best


def cluster_coverage(resume_pool: set, jd_pool: set) -> dict:
    """
    For each cluster that appears in the JD, calculate what fraction
    of its JD members the resume covers (with transferable credit).
    Returns {cluster_name: {coverage, jd_count, resume_count, matched, transferable}}
    """
    results = {}
    for cluster_name, cluster in SKILL_CLUSTERS.items():
        # Which cluster members appear in the JD?
        jd_cluster_skills = [s for s in cluster['members'] if
                              s in jd_pool or
                              any(stem(s) == stem(t) for t in jd_pool)]
        if not jd_cluster_skills:
            continue

        exact_matched = []
        transfer_matched = []
        total_credit = 0.0

        for skill in jd_cluster_skills:
            score = transferable_score(skill, resume_pool)
            if score >= 0.95:
                exact_matched.append(skill)
                total_credit += 1.0
            elif score > 0:
                transfer_matched.append(skill)
                total_credit += score

        coverage = total_credit / len(jd_cluster_skills) if jd_cluster_skills else 0.0
        results[cluster_name] = {
            'coverage': round(coverage * 100, 1),
            'jd_count': len(jd_cluster_skills),
            'matched_exact': exact_matched,
            'matched_transfer': transfer_matched,
            'missing': [s for s in jd_cluster_skills
                        if s not in exact_matched and s not in transfer_matched],
        }

    return results

# ---------------------------------------------------------------------------
# Section-aware scoring with transferable credit
# ---------------------------------------------------------------------------

def score_section(section_text: str, jd_pool: set, jd_skills: set) -> float:
    """
    Measure how well a section covers the JD using transferable credit.
    Returns [0, 1].
    """
    if not section_text.strip():
        return 0.0
    sec_pool = get_token_pool(section_text)
    if not jd_skills:
        return 0.0

    total = 0.0
    for skill in jd_skills:
        total += transferable_score(skill, sec_pool)

    return total / len(jd_skills)


def compute_section_scores(sections: dict, jd_pool: set, jd_skills: set) -> dict:
    scores = {}
    for sec in ['skills', 'experience', 'projects', 'education', 'certifications', 'summary']:
        scores[sec] = round(score_section(sections.get(sec, ''), jd_pool, jd_skills) * 100, 1)
    return scores

# ---------------------------------------------------------------------------
# Keyword-level ATS matching (with soft/transferable credit)
# ---------------------------------------------------------------------------

def compute_keyword_match(jd_pool: set, resume_pool: set) -> dict:
    """
    For every JD keyword compute an exact or transferable match score.
    Returns matched, partial, missing lists and an overall coverage %.
    """
    matched_exact = []
    matched_partial = []
    missing = []

    for kw in sorted(jd_pool):
        score = transferable_score(kw, resume_pool)
        if score >= 0.95:
            matched_exact.append(kw)
        elif score >= 0.4:
            matched_partial.append({'keyword': kw, 'credit': round(score, 2)})
        else:
            missing.append(kw)

    total = len(jd_pool)
    exact_count = len(matched_exact)
    partial_credit = sum(p['credit'] for p in matched_partial)
    effective_matched = exact_count + partial_credit

    # Concave (square-root) coverage so missing a few keywords doesn't crater the score.
    # Linear:   50% matched → 50 coverage
    # Concave:  50% matched → 71 coverage  (sqrt(0.5) * 100)
    # This means getting the core skills matters far more than having every single keyword.
    linear_ratio = effective_matched / total if total else 0.0
    concave_ratio = math.sqrt(linear_ratio)
    coverage = round(concave_ratio * 100, 1)

    return {
        'matched_exact': matched_exact,
        'matched_partial': matched_partial,
        'missing': missing,
        'coverage': coverage,
        'total_jd_keywords': total,
        'effective_matched': round(effective_matched, 1),
        'linear_coverage': round(linear_ratio * 100, 1),
    }

# ---------------------------------------------------------------------------
# Score calibration
# Stretch raw [0,1] into recruiter-scale bands:
#   excellent → 80–95, strong → 70–85, moderate → 50–70, weak → 20–50
# ---------------------------------------------------------------------------

def calibrate_score(raw: float) -> float:
    """
    Generous piecewise calibration — rewards partial coverage, doesn't punish
    for missing non-essential keywords.

    Mapping (raw → calibrated):
      0%  →  0%   (truly empty / no match)
      20% → 38%   (weak but some alignment)
      40% → 58%   (moderate — half the essentials)
      60% → 72%   (strong — most essentials covered)
      80% → 84%   (excellent)
     100% → 95%   (near-perfect)
    """
    r = raw / 100.0
    if r <= 0.0:
        return 0.0
    if r >= 1.0:
        return 95.0

    breakpoints = [
        (0.00,  0.0),
        (0.20, 38.0),
        (0.40, 58.0),
        (0.60, 72.0),
        (0.80, 84.0),
        (1.00, 95.0),
    ]
    for i in range(len(breakpoints) - 1):
        r0, s0 = breakpoints[i]
        r1, s1 = breakpoints[i + 1]
        if r0 <= r <= r1:
            t = (r - r0) / (r1 - r0)
            return round(s0 + t * (s1 - s0), 1)
    return round(raw, 1)

# ---------------------------------------------------------------------------
# Confidence / reasoning engine
# ---------------------------------------------------------------------------

def build_confidence_reasoning(
    cluster_results: dict,
    section_scores: dict,
    keyword_result: dict,
    sections: dict,
) -> dict:
    """
    Produce human-readable reasoning bullets for the UI.
    """
    reasons = {
        'matched_clusters': [],
        'partial_clusters': [],
        'missing_clusters': [],
        'experience_found': False,
        'experience_notes': [],
        'projects_found': False,
        'project_notes': [],
        'missing_critical': [],
        'strengths': [],
    }

    # Cluster reasoning
    for cname, data in cluster_results.items():
        cov = data['coverage']
        if cov >= 70:
            reasons['matched_clusters'].append({
                'cluster': cname,
                'coverage': cov,
                'skills': data['matched_exact'],
            })
            if cov >= 80:
                reasons['strengths'].append(
                    f"Strong {cname} coverage ({cov}%) — {', '.join(data['matched_exact'][:4])}"
                )
        elif cov >= 30:
            reasons['partial_clusters'].append({
                'cluster': cname,
                'coverage': cov,
                'matched': data['matched_exact'] + data['matched_transfer'],
                'missing': data['missing'],
            })
        else:
            reasons['missing_clusters'].append({
                'cluster': cname,
                'coverage': cov,
                'missing': data['missing'],
            })
            if data['jd_count'] >= 2:
                reasons['missing_critical'].append(
                    f"{cname}: missing {', '.join(data['missing'][:3])}"
                )

    # Experience reasoning
    exp_score = section_scores.get('experience', 0)
    reasons['experience_found'] = exp_score >= 30
    if exp_score >= 70:
        reasons['experience_notes'].append('Strong experience alignment with the role requirements.')
    elif exp_score >= 40:
        reasons['experience_notes'].append('Relevant experience found; some gaps with JD specifics.')
    elif sections.get('experience', '').strip():
        reasons['experience_notes'].append('Experience section present but limited keyword overlap with JD.')
    else:
        reasons['experience_notes'].append('No distinct experience section detected.')

    # Projects reasoning
    proj_score = section_scores.get('projects', 0)
    reasons['projects_found'] = proj_score >= 25
    if proj_score >= 60:
        reasons['project_notes'].append('Projects demonstrate relevant technical skills.')
    elif proj_score >= 25:
        reasons['project_notes'].append('Some relevant projects found.')
    elif sections.get('projects', '').strip():
        reasons['project_notes'].append('Projects present but do not strongly mirror JD requirements.')
    else:
        reasons['project_notes'].append('No distinct projects section detected.')

    # Missing critical keywords — filter to real skill-like terms only (no noise bigrams)
    if keyword_result['missing'] and not reasons['missing_critical']:
        skill_missing = [
            kw for kw in keyword_result['missing']
            if (
                find_cluster(kw) is not None or
                len(kw) >= 4
            ) and ' ' not in kw  # exclude noisy bigrams
        ]
        if skill_missing:
            reasons['missing_critical'].append(
                f"Missing keywords: {', '.join(skill_missing[:6])}"
            )

    return reasons

# ---------------------------------------------------------------------------
# Master compute function
# ---------------------------------------------------------------------------

def compute_match(resume_text: str, jd_text: str) -> dict:
    # 1 – Section splitting
    sections = split_into_sections(resume_text)

    # 2 – Token pools
    resume_pool = get_token_pool(resume_text)
    jd_pool = get_token_pool(jd_text)

    # 3 – Extract skills from JD (tokens that appear in any cluster)
    jd_skills = {t for t in jd_pool if find_cluster(t) is not None or len(t) > 3}

    # 4 – Cluster coverage analysis
    cluster_results = cluster_coverage(resume_pool, jd_pool)

    # 5 – Keyword-level match (with soft/transferable credit)
    keyword_result = compute_keyword_match(jd_pool, resume_pool)

    # 6 – Section scores
    section_scores = compute_section_scores(sections, jd_pool, jd_skills)

    # 7 – Weighted composite (new weights: Skills 35, Exp 35, Proj 20, Edu/Cert 10)
    weighted_raw = sum(
        (section_scores.get(sec, 0) / 100) * weight
        for sec, weight in SECTION_WEIGHTS.items()
    )
    weighted_score = round(weighted_raw * 100, 1)

    # 8 – Cluster score: average coverage across JD-relevant clusters
    cluster_score = 0.0
    if cluster_results:
        cluster_score = sum(c['coverage'] for c in cluster_results.values()) / len(cluster_results)

    # 9 – Raw blended score
    # Weights: cluster coverage is the most lenient (grouped, transferable) signal so
    # we give it the highest share. Keyword coverage already uses a concave curve.
    # 30% keyword coverage + 30% weighted sections + 40% cluster coverage
    kw_coverage = keyword_result['coverage']
    raw_blended = (0.30 * kw_coverage + 0.30 * weighted_score + 0.40 * cluster_score)

    # 10 – Calibrate into recruiter scale
    final_score = calibrate_score(raw_blended)

    # 11 – Confidence reasoning
    reasoning = build_confidence_reasoning(cluster_results, section_scores, keyword_result, sections)

    # 12 – ATS-style score (raw keyword coverage before calibration)
    ats_score = round(kw_coverage, 1)

    return {
        'match_percentage': final_score,
        'ats_score': ats_score,
        'keyword_coverage': round(kw_coverage, 1),
        'experience_match': section_scores.get('experience', 0),
        'projects_match': section_scores.get('projects', 0),
        'weighted_score': weighted_score,
        'cluster_score': round(cluster_score, 1),

        # Keyword results
        'matched_keywords': keyword_result['matched_exact'],
        'partial_keywords': keyword_result['matched_partial'],
        'missing_keywords': keyword_result['missing'],

        # Section breakdown
        'section_scores': section_scores,

        # Cluster breakdown
        'cluster_results': cluster_results,

        # Confidence reasoning
        'reasoning': reasoning,

        # Debug
        'debug': {
            'total_jd_keywords': keyword_result['total_jd_keywords'],
            'total_matched': len(keyword_result['matched_exact']),
            'partial_matched': len(keyword_result['matched_partial']),
            'effective_matched': keyword_result['effective_matched'],
            'sections_found': list(sections.keys()),
            'raw_blended': round(raw_blended, 1),
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

    return jsonify(compute_match(resume_text, jd_text))


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=False)
