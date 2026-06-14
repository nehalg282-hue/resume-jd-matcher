"""
scoring.py
Keyword-level ATS matching, section scoring, and the final score calibration.
"""
import math

from .constants import SECTION_WEIGHTS
from .text_processing import get_token_pool
from .skill_matcher import transferable_score


def compute_keyword_match(jd_pool: set, resume_pool: set) -> dict:
    """
    Score every JD keyword against the resume using exact + transferable matching.

    Coverage uses a square-root (concave) curve so that missing a few keywords
    doesn't crater the score — getting the core skills earns most of the credit.

    Returns:
        matched_exact   – list of keywords with full credit
        matched_partial – list of {keyword, credit} with transferable credit
        missing         – list of unmatched keywords
        coverage        – concave coverage score [0–100]
        linear_coverage – raw linear ratio [0–100] (for debug display)
        total_jd_keywords, effective_matched
    """
    matched_exact: list = []
    matched_partial: list = []
    missing: list = []

    for kw in sorted(jd_pool):
        score = transferable_score(kw, resume_pool)
        if score >= 0.95:
            matched_exact.append(kw)
        elif score >= 0.4:
            matched_partial.append({'keyword': kw, 'credit': round(score, 2)})
        else:
            missing.append(kw)

    total = len(jd_pool)
    effective_matched = len(matched_exact) + sum(p['credit'] for p in matched_partial)
    linear_ratio = effective_matched / total if total else 0.0

    # Concave curve: sqrt(ratio)
    # At 50% linear → ~71% concave; at 70% linear → ~84% concave
    concave_ratio = math.sqrt(linear_ratio)

    return {
        'matched_exact': matched_exact,
        'matched_partial': matched_partial,
        'missing': missing,
        'coverage': round(concave_ratio * 100, 1),
        'linear_coverage': round(linear_ratio * 100, 1),
        'total_jd_keywords': total,
        'effective_matched': round(effective_matched, 1),
    }


def score_section(section_text: str, jd_pool: set, jd_skills: set) -> float:
    """
    Measure how well one resume section covers JD skills using transferable credit.
    Returns a ratio in [0.0, 1.0].
    """
    if not section_text.strip() or not jd_skills:
        return 0.0
    sec_pool = get_token_pool(section_text)
    total = sum(transferable_score(skill, sec_pool) for skill in jd_skills)
    return total / len(jd_skills)


def compute_section_scores(sections: dict, jd_pool: set, jd_skills: set) -> dict:
    """
    Return per-section match percentages for all tracked sections.
    """
    return {
        sec: round(
            score_section(sections.get(sec, ''), jd_pool, jd_skills) * 100, 1
        )
        for sec in ['skills', 'experience', 'projects', 'education', 'certifications', 'summary']
    }


def compute_weighted_score(section_scores: dict) -> float:
    """
    Combine section scores into a single weighted percentage using SECTION_WEIGHTS.
    """
    raw = sum(
        (section_scores.get(sec, 0) / 100) * weight
        for sec, weight in SECTION_WEIGHTS.items()
    )
    return round(raw * 100, 1)


def calibrate_score(raw: float) -> float:
    """
    Generous piecewise-linear calibration that maps a raw blended score [0–100]
    to a recruiter-realistic final score.

    Designed so that having ~half the essentials still lands in the moderate band,
    and missing non-critical keywords is not heavily penalised.

    Mapping:
       0% →  0%   (no relevant content)
      20% → 38%   (weak, some alignment)
      40% → 58%   (moderate, half the essentials)
      60% → 72%   (strong, most essentials)
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
