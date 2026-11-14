from groq_client import generate_cv_description, get_groq_client
LIST_FIELDS = {"skills", "target_roles", "certifications"}


def apply_overrides(profile: dict, updates: dict):
    for key, value in updates.items():
        if key in LIST_FIELDS:
            existing = profile.get(key) or []
            profile[key] = existing + [v for v in value if v not in existing]
        else:
            profile[key] = value
    
    
def update_cv_profile(
    seniority: str = None,
    experience_years: float = None,
    skills: list = None,
    target_roles: list = None,
    certifications: list = None,
    state: dict = None,
):
    """Saves user corrections to the CV profile so matching can use them."""
    updates = {
        "seniority": seniority,
        "experience_years": experience_years,
        "skills": skills,
        "target_roles": target_roles,
        "certifications": certifications,
    }
    updates = {k: v for k, v in updates.items() if v is not None}

    if not updates:
        return {"status": "error", "message": "No profile fields were provided."}

    apply_overrides(state["cv_overrides"], updates)
    if state.get("cv_profile"):
        apply_overrides(state["cv_profile"], updates)
    state["last_matches"] = []

    return {"status": "success", "updated": updates, "all_overrides": state["cv_overrides"]}

def get_cv_profile(state: dict = None):
    """Returns the key fields of the user's CV profile."""
    if not state or not state.get("cv_text"):
        return {"status": "error", "message": "No CV uploaded. Ask the user to upload one."}
    if not state.get("cv_profile"):
        state["cv_profile"] = generate_cv_description(
            state["cv_text"], client=get_groq_client()
        ).model_dump()
    profile = state["cv_profile"]
    apply_overrides(profile, state.get("cv_overrides", {}))
    return {
        "status": "success",
        "profile": {
            "full_name": profile.get("full_name"),
            "location": profile.get("location"),
            "seniority": profile.get("seniority"),
            "experience_years": profile.get("experience_years"),
            "target_roles": profile.get("target_roles"),
            "skills": profile.get("skills"),
            "languages": profile.get("languages"),
            "summary": profile.get("summary"),
            "certifications": profile.get("certifications"),
            "education": [
                {"degree": e.get("degree"), "institution": e.get("institution")}
                for e in profile.get("education") or []
                if isinstance(e, dict)
            ],
            "experience": [
                {
                    "title": e.get("title"),
                    "company": e.get("company"),
                    "duration_months": e.get("duration_months"),
                }
                for e in profile.get("experience") or []
                if isinstance(e, dict)
            ],
            "projects": [
                {"name": p.get("name"), "technologies": p.get("technologies")}
                for p in profile.get("projects") or []
                if isinstance(p, dict)
            ],
        }
    }
