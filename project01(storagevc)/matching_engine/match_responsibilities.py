from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


def match_responsibilities(cv_resp, job_resp, model,THRESHHOLD=0.50):

    if not job_resp:
        return 1.0

    if not cv_resp:
        return 0.0

    job_resp_embedding = model.encode(job_resp)
    cv_resp_embedding = model.encode(cv_resp)

    similarities = cosine_similarity(
        job_resp_embedding,
        cv_resp_embedding
    )

    best_matches = similarities.max(axis=1)
    best_matches_indices = similarities.argmax(axis=1)

    matches = []

    for job_index, cv_index in enumerate(best_matches_indices):

        job_text = job_resp[job_index]
        original_similarity = best_matches[job_index]
        cv_text = cv_resp[cv_index]
        if original_similarity >= THRESHHOLD:
            passed = True
        else:
            best_matches[job_index] = 0
            passed = False

        matches.append({
            "job_responsibility": job_text,
            "cv_responsibility": cv_text,
            "similarity": float(best_matches[job_index]),
            "passed_Threshhold": passed,
            "Raw Similarity": float(original_similarity)
        })
    score = float(best_matches.mean())

    return {
        "score": score,
        "matches": matches
    }