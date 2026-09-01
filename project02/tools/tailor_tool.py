# tools/match_tool.py
import os
import json
import settings
from qDrantStore import connect
from matching_engine.match_job import match_job
from groq_client import generate_tailored_recommendation

def match_all_jobs(limit: int = 5, state: dict = None):
    """Matches stored jobs against CV profile and saves results to state."""
    try:
        client = connect()
        cv_path = settings.P1_ROOT / "cv_profile.json"
        with open(cv_path, "r", encoding="utf-8") as f:
            cv_profile = json.load(f)

        records, _ = client.scroll(
            collection_name=os.getenv("COLLECTION_NAME", "jobs"),
            limit=60,
            with_payload=True
        )

        results = []
        for r in records:
            payload = r.payload or {}
            job_profile = payload.get("profile") or {}
            raw_job = payload.get("raw_job") or {}
            score = match_job(job_profile=job_profile, cv_profile=cv_profile)
            if score["final_score"] > 0:
                results.append({"match_score": score, "raw_job": raw_job})

        results.sort(key=lambda x: x["match_score"]["final_score"], reverse=True)
        top_matches = results[:limit]

        # Update shared state for tailor_cv to use
        if state is not None:
            state["last_matches"] = top_matches

        return {"status": "success", "count": len(top_matches), "matches": top_matches}
    except Exception as e:
        return {"status": "error", "message": f"Matching failed: {str(e)}"}



def tailor_cv(top_n: int = 3, state: dict = None):
    """Tailors CV recommendations for the best matches stored in state."""
    try:
        if not state or not state.get("last_matches"):
            return {
                "status": "error",
                "message": "No match results found in memory. Please run match_all_jobs first."
            }
        cv_path = settings.P1_ROOT / "resources" / "cv.txt"
        with open(cv_path, "r", encoding="utf-8") as f:
            cv_text = f.read()
        matches_to_tailor = state["last_matches"][:top_n]
        recommendations = generate_tailored_recommendation(
            cv_text=cv_text,
            top_matches=matches_to_tailor
        )
        return {"status": "success", "recommendations": recommendations}
    except Exception as e:
        return {"status": "error", "message": f"Tailoring failed: {str(e)}"}