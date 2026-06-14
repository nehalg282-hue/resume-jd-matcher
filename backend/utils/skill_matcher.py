"""
skill_matcher.py
Skill cluster definitions, transferable-skill lookup, and cluster-level
coverage scoring with partial credit for related technologies.
"""
from .constants import SKILL_CLUSTERS
from .text_processing import stem


def find_cluster(skill: str) -> str | None:
    """Return the cluster name that contains `skill`, or None if not found."""
    for cluster_name, cluster in SKILL_CLUSTERS.items():
        if skill in cluster['members']:
            return cluster_name
    return None


def transferable_score(wanted: str, resume_pool: set) -> float:
    """
    Return a [0.0, 1.0] match score for `wanted` against the resume token pool.

    - 1.0  → exact token match or same stem
    - 0.4–0.9 → transferable credit from a related skill in the same cluster
    - 0.0  → no match

    Examples:
      wanted='react',      resume has 'nextjs'      → 0.90
      wanted='postgres',   resume has 'mysql'       → 0.80
      wanted='docker',     resume has 'kubernetes'  → 0.70
      wanted='typescript', resume has 'javascript'  → 0.80
    """
    # Exact token or stem match
    if wanted in resume_pool or any(stem(wanted) == stem(t) for t in resume_pool):
        return 1.0

    # Transferable credit from cluster definitions
    best = 0.0
    for cluster in SKILL_CLUSTERS.values():
        for alt, credit in cluster['transferable'].get(wanted, []):
            if alt in resume_pool or any(stem(alt) == stem(t) for t in resume_pool):
                best = max(best, credit)

    return best


def cluster_coverage(resume_pool: set, jd_pool: set) -> dict:
    """
    For every skill cluster that has at least one member appearing in the JD,
    compute how well the resume covers that cluster (with transferable credit).

    Returns:
        {
          cluster_name: {
            'coverage':         float (0–100),
            'jd_count':         int,
            'matched_exact':    list[str],
            'matched_transfer': list[str],
            'missing':          list[str],
          }
        }
    """
    results = {}
    for cluster_name, cluster in SKILL_CLUSTERS.items():
        jd_cluster_skills = [
            s for s in cluster['members']
            if s in jd_pool or any(stem(s) == stem(t) for t in jd_pool)
        ]
        if not jd_cluster_skills:
            continue

        exact_matched: list = []
        transfer_matched: list = []
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
            'missing': [
                s for s in jd_cluster_skills
                if s not in exact_matched and s not in transfer_matched
            ],
        }

    return results
