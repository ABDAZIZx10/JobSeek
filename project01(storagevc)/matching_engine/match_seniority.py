SENIORITY_LVL = {
    "entry level": 1,
    "junior": 2,
    "mid": 3,
    "mid-senior level": 4,
    "senior": 5,
    "lead": 6,
    "manager": 6,
    "director": 7,
}


def normalize_sen(lvl):
    if isinstance(lvl, int):
        return lvl
    if isinstance(lvl, str):
        return SENIORITY_LVL.get(lvl.lower().strip())
    return None

def match_seniority(cv_sen, job_sen):
    if job_sen is None:
        score = 1.0
        print(f"[Seniority Match] No job seniority required | Score: {score:.2f}")
        return score

    cv_lvl = normalize_sen(cv_sen)
    job_lvl = normalize_sen(job_sen)

    if cv_lvl is None or job_lvl is None:
        score = 1.0
    elif cv_lvl >= job_lvl:
        score = 1.0
    else:
        score = cv_lvl / job_lvl

    print(f"[Seniority Match] Candidate: {cv_sen} (Lvl {cv_lvl}) | Job: {job_sen} (Lvl {job_lvl}) | Score: {score:.2f}")
    return score
