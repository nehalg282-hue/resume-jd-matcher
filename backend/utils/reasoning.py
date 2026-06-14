"""
reasoning.py
Generates human-readable confidence reasoning bullets used by the frontend
to explain the match score in recruiter-friendly language.
"""
from .skill_matcher import find_cluster


def build_confidence_reasoning(
    cluster_results: dict,
    section_scores: dict,
    keyword_result: dict,
    sections: dict,
) -> dict:
    """
    Analyse cluster results and section scores to produce structured reasoning.

    Returns a dict with:
        matched_clusters  – clusters with ≥70% coverage
        partial_clusters  – clusters with 30–70% coverage
        missing_clusters  – clusters with <30% coverage
        experience_found  – bool
        experience_notes  – list[str]
        projects_found    – bool
        project_notes     – list[str]
        missing_critical  – list[str] describing gaps
        strengths         – list[str] highlight sentences
    """
    reasons: dict = {
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

    # ── Cluster reasoning ────────────────────────────────────────────────────
    for cname, data in cluster_results.items():
        cov = data['coverage']
        if cov >= 70:
            reasons['matched_clusters'].append({
                'cluster': cname,
                'coverage': cov,
                'skills': data['matched_exact'],
            })
            if cov >= 80:
                top = ', '.join(data['matched_exact'][:4])
                reasons['strengths'].append(
                    f"Strong {cname} coverage ({cov}%) — {top}"
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
                top_missing = ', '.join(data['missing'][:3])
                reasons['missing_critical'].append(
                    f"{cname}: missing {top_missing}"
                )

    # ── Experience reasoning ─────────────────────────────────────────────────
    exp_score = section_scores.get('experience', 0)
    reasons['experience_found'] = exp_score >= 30
    if exp_score >= 70:
        reasons['experience_notes'].append(
            'Strong experience alignment with the role requirements.'
        )
    elif exp_score >= 40:
        reasons['experience_notes'].append(
            'Relevant experience found; some gaps with JD specifics.'
        )
    elif sections.get('experience', '').strip():
        reasons['experience_notes'].append(
            'Experience section present but limited keyword overlap with JD.'
        )
    else:
        reasons['experience_notes'].append(
            'No distinct experience section detected.'
        )

    # ── Projects reasoning ───────────────────────────────────────────────────
    proj_score = section_scores.get('projects', 0)
    reasons['projects_found'] = proj_score >= 25
    if proj_score >= 60:
        reasons['project_notes'].append('Projects demonstrate relevant technical skills.')
    elif proj_score >= 25:
        reasons['project_notes'].append('Some relevant projects found.')
    elif sections.get('projects', '').strip():
        reasons['project_notes'].append(
            'Projects present but do not strongly mirror JD requirements.'
        )
    else:
        reasons['project_notes'].append('No distinct projects section detected.')

    # ── Missing critical keywords ────────────────────────────────────────────
    # Only surface real skill-like single tokens (no noisy bigrams)
    if keyword_result['missing'] and not reasons['missing_critical']:
        skill_missing = [
            kw for kw in keyword_result['missing']
            if (find_cluster(kw) is not None or len(kw) >= 4) and ' ' not in kw
        ]
        if skill_missing:
            reasons['missing_critical'].append(
                f"Missing keywords: {', '.join(skill_missing[:6])}"
            )

    return reasons
