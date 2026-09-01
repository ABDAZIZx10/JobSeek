from model_provider import get_model
from matching_engine.match_skills import match_skills
from matching_engine.match_experience import match_experience
from matching_engine.match_seniority import match_seniority, SENIORITY_LVL
from matching_engine.match_responsibilities import match_responsibilities


        
    
         

def match_job(job_profile, cv_profile: dict):

    SKILL_WEIGHT = 35
    RESPONSIBILITY_WEIGHT = 30
    EXPERIENCE_WEIGHT = 20
    SENIORITY_WEIGHT = 15



    
    model = get_model()
    
    # Safely extract CV responsibilities
    if isinstance(cv_profile, dict):
        cv_resp = [
            resp
            for exp in cv_profile.get("experience", [])
            for resp in (exp.get("responsibilities", []) if isinstance(exp, dict) else getattr(exp, "responsibilities", []))
        ]
        cv_experience = cv_profile.get("experience_years", 0)
        cv_skills = cv_profile.get("skills", [])
        cv_seniority = cv_profile.get("seniority", None)
    else:
        cv_resp = [
            resp
            for exp in getattr(cv_profile, "experience", [])
            for resp in getattr(exp, "responsibilities", [])
        ]
        cv_experience = getattr(cv_profile, "experience_years", 0)
        cv_skills = getattr(cv_profile, "skills", [])
        cv_seniority = getattr(cv_profile, "seniority", None)

    # Fallback to mapping years if seniority string is missing
    if cv_seniority is None:
        cv_seniority = next((k for k, v in SENIORITY_LVL.items() if v == int(cv_experience)), None)

    #job extraction:
    job_resp = job_profile.get("responsibilities", [])
    if not job_resp:
        RESPONSIBILITY_WEIGHT = 0
    job_experience = job_profile.get("experience_years")
    if  job_experience is None:
            job_experience = 0
            EXPERIENCE_WEIGHT = 0
    else:
        job_experience = int(job_profile.get("experience_years", 0))
    job_seniority = job_profile.get("seniority", None)
    if not job_seniority:
            SENIORITY_WEIGHT = 0
    job_skills = job_profile.get("required_skills", []) + job_profile.get("preferred_skills", [])
    if not job_skills:
        SKILL_WEIGHT = 0
    
    print("\n================ START MATCHING JOB ================")
    if RESPONSIBILITY_WEIGHT:
        responsibilities_score = match_responsibilities(cv_resp=cv_resp, job_resp=job_resp, THRESHHOLD=0.65, model=model)
    else:
        responsibilities_score = 0
    if EXPERIENCE_WEIGHT:
        experience_score = match_experience(cv_experience=cv_experience, job_experience=job_experience)
    else:
        experience_score = 0
    if SKILL_WEIGHT:
        skills_score = match_skills(cv_skills=cv_skills, job_skills=job_skills)
    else:
        skills_score = 0
    if SENIORITY_WEIGHT:
        seniority_score = match_seniority(cv_sen=cv_seniority, job_sen=job_seniority)
    else:
        seniority_score = 0
    # Extract numerical scores for weighting
    skills_val = skills_score["score"] if isinstance(skills_score, dict) else skills_score
    resp_val = responsibilities_score["score"] if isinstance(responsibilities_score, dict) else responsibilities_score
    exp_val = experience_score["score"] if isinstance(experience_score, dict) else experience_score
    sen_val = seniority_score["score"] if isinstance(seniority_score, dict) else seniority_score
    
    final_weight = SKILL_WEIGHT +RESPONSIBILITY_WEIGHT + EXPERIENCE_WEIGHT + SENIORITY_WEIGHT
    
    if final_weight == 0:
        return {
            "final_score": 0,
            "breakdown": {}
        }
    
    skill_weighted = skills_val * SKILL_WEIGHT / final_weight
    resp_weighted = resp_val * RESPONSIBILITY_WEIGHT / final_weight
    exp_weighted = exp_val * EXPERIENCE_WEIGHT / final_weight
    sen_weighted = sen_val * SENIORITY_WEIGHT / final_weight

    final_score = skill_weighted + resp_weighted + exp_weighted + sen_weighted

    print("\n--- Weighted Match Summary ---")
    print(f"  • Skills ({SKILL_WEIGHT / final_weight:.2f}%):         {skills_val:.2f} -> {skill_weighted:.4f}")
    print(f"  • Responsibilities ({RESPONSIBILITY_WEIGHT / final_weight:.2f}%): {resp_val:.2f} -> {resp_weighted:.4f}")
    print(f"  • Experience ({EXPERIENCE_WEIGHT / final_weight:.2f}%):     {exp_val:.2f} -> {exp_weighted:.4f}")
    print(f"  • Seniority ({SENIORITY_WEIGHT / final_weight:.2f}%):      {sen_val:.2f} -> {sen_weighted:.4f}")
    print(f"--> FINAL MATCH SCORE: {final_score:.4f} ({final_score*100:.2f}%)\n====================================================\n")
    
    return {
        "final_score": round(final_score, 4),
        "breakdown": {
            "skills": skills_score,
            "responsibilities": responsibilities_score,
            "experience": experience_score,
            "seniority": seniority_score
        },
        
    }