def match_experience(cv_experience, job_experience):
    if not job_experience or cv_experience >= job_experience:
        score = 1.0
    else:
        score = cv_experience / job_experience
    return {
        "score": score,
        "required": job_experience,
        "candidate": cv_experience
    }