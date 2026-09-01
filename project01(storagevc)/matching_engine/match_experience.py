def match_experience(cv_experience, job_experience):
    if not job_experience or cv_experience >= job_experience:
        score = 1.0
    else:
        score = cv_experience / job_experience
    print(f"[Experience Match] Candidate: {cv_experience} yrs | Required: {job_experience} yrs | Score: {score:.2f}")
    return {
        "score": score,
        "required": job_experience,
        "candidate": cv_experience
    }