import os
from qDrantStore import connect
from matching_engine.match_job import match_job
from groq_client import generate_tailored_recommendation, generate_cv_description, get_groq_client


def match_all_jobs(limit: int = 5, state: dict = None):
    """Matches stored jobs against CV profile and saves results to state."""
    try:
        if not state or not state.get("cv_text"):
            return {
                "status": "error",
                "message": "No CV uploaded. Ask the user to upload a CV (PDF, DOCX, or TXT) in the UI first.",
            }

        if not state.get("cv_profile"):
            client = get_groq_client()
            state["cv_profile"] = generate_cv_description(
                state["cv_text"],
                client=client,
            ).model_dump()

        cv_profile = state["cv_profile"]
        qdrant = connect()
        collection = os.getenv("COLLECTION_NAME", "linkedIn_jobs")

        results = []
        offset = None
        while True:
            records, offset = qdrant.scroll(
                collection_name=collection,
                offset=offset,
                limit=60,
                with_payload=True,
                with_vectors=False,
            )
            for record in records:
                payload = record.payload or {}
                job_profile = payload.get("profile") or {}
                raw_job = payload.get("raw_job") or {}
                score = match_job(job_profile=job_profile, cv_profile=cv_profile)
                if score.get("final_score", 0) > 0:
                    results.append({"match_score": score, "raw_job": raw_job})
            if offset is None:
                break

        results.sort(key=lambda x: x["match_score"]["final_score"], reverse=True)
        top_matches = results[:limit]
        state["last_matches"] = top_matches

        slim = [
            {
                "title": m["raw_job"].get("title"),
                "company": m["raw_job"].get("company"),
                "location": m["raw_job"].get("location"),
                "url": m["raw_job"].get("Job Details URL"),
                "score": m["match_score"].get("final_score"),
            }
            for m in top_matches
        ]
        return {"status": "success", "count": len(top_matches), "matches": slim}
    except Exception as e:
        return {"status": "error", "message": f"Matching failed: {str(e)}"}


def tailor_cv(top_n: int = 3, state: dict = None):
    """Tailors CV recommendations for the best matches stored in state."""
    try:
        if not state or not state.get("last_matches"):
            return {
                "status": "error",
                "message": "No match results found in memory. Please run match_all_jobs first.",
            }
        if not state.get("cv_text"):
            return {
                "status": "error",
                "message": "No CV uploaded. Ask the user to upload a CV in the UI first.",
            }

        matches_to_tailor = state["last_matches"][:top_n]
        recommendations = generate_tailored_recommendation(
            cv_text=state["cv_text"],
            top_matches=matches_to_tailor,
        )
        return {"status": "success", "recommendations": recommendations}
    except Exception as e:
        return {"status": "error", "message": f"Tailoring failed: {str(e)}"}
