import re

ALIASES = {
    "postgresql": "postgres",
    "postgres": "postgres",
    "js": "javascript",
    "javascript": "javascript",
    "nodejs": "node",
    "node": "node",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "ts": "typescript",
    "typescript": "typescript",
    "reactjs": "react",
    "react": "react",
    "mongodb": "mongo",
    "mongo": "mongo",
    "golang": "go",
    "go": "go",
    "rest api": "rest api",
    "rest apis": "rest api",
    "restful api": "rest api",
}


def normalize_skill(skill: str) -> str:
    text = skill.lower().strip()
    text = text.replace(".", "")
    text = re.sub(r"[^a-z0-9+#]+", " ", text)
    text = " ".join(text.split())
    return ALIASES.get(text, text)


def _score_skill_list(cv_set: set[str], job_skills: list[str]) -> dict:
    if not job_skills:
        return {
            "score": 0.0,
            "matched": 0,
            "total": 0,
            "matched_skills": [],
        }

    matched_skills = [
        skill
        for skill in job_skills
        if normalize_skill(skill) in cv_set
    ]
    score = len(matched_skills) / len(job_skills)
    return {
        "score": score,
        "matched": len(matched_skills),
        "total": len(job_skills),
        "matched_skills": matched_skills,
    }


def match_skills(cv_skills, required_skills=None, preferred_skills=None, job_skills=None):
    """
    Normalize-only skill matching.
    Prefer required_skills / preferred_skills; job_skills kept for backward compatibility.
    """
    if required_skills is None and preferred_skills is None:
        required_skills = job_skills or []
        preferred_skills = []
    else:
        required_skills = required_skills or []
        preferred_skills = preferred_skills or []

    if not required_skills and not preferred_skills:
        return {
            "score": 0.0,
            "matched": 0,
            "total": 0,
            "matched_skills": [],
            "required_score": 0.0,
            "preferred_score": 0.0,
        }

    cv_set = {normalize_skill(skill) for skill in (cv_skills or [])}

    required_result = _score_skill_list(cv_set, required_skills)
    preferred_result = _score_skill_list(cv_set, preferred_skills)

    if required_skills and preferred_skills:
        score = 0.7 * required_result["score"] + 0.3 * preferred_result["score"]
    elif required_skills:
        score = required_result["score"]
    else:
        score = preferred_result["score"]

    matched_skills = required_result["matched_skills"] + preferred_result["matched_skills"]
    total = required_result["total"] + preferred_result["total"]

    return {
        "score": score,
        "matched": len(matched_skills),
        "total": total,
        "matched_skills": matched_skills,
        "required_score": required_result["score"],
        "preferred_score": preferred_result["score"],
    }
