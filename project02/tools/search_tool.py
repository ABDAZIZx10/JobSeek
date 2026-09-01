import settings
from embed_jobs import Search

def search_jobs(query: str, limit: int = 5):
    """Searches jobs in Qdrant matching query semantically."""
    try:
        results = Search(query=query, limit=limit)
        return {"status": "success", "count": len(results), "jobs": results}
    except Exception as e:
        return {"status": "error", "message": f"Search failed: {str(e)}"}
