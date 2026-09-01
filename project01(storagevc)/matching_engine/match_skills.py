def match_skills(cv_skills, job_skills):
    if not job_skills:
        score = 0
        print(f"[Skills Match] No required skills specified | Score: {score:.2f}")
        return {"score": score, "matched": 0, "total": 0}

    matched_skills = [skill for skill in cv_skills if skill in job_skills]
    score = len(matched_skills) / len(job_skills)
    
    print(f"[Skills Match] Matched {len(matched_skills)}/{len(job_skills)} skills | Score: {score:.2f}")
    return {
        "score": score,
        "matched": len(matched_skills),
        "total": len(job_skills)}
