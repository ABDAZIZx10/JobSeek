import settings
from embed_jobs import Search

def search_jobs(query: str, limit: int = 5):
    """Searches jobs in Qdrant matching query semantically."""
    try:
        results = Search(query=query, limit=limit)
        slim_jobs = [
            {
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "url": job.get("url"),
                "score": job.get("score"),
            }
            for job in results
            ]

        return {"status": "success", "count": len(results), "jobs": slim_jobs}
    except Exception as e:
        return {"status": "error", "message": f"Search failed: {str(e)}"}
