import os
import settings  # loads P1 sys.path & env
from qDrantStore import connect

def get_job_stats():
    """Returns the total number of jobs currently in Qdrant."""
    try:
        client = connect()
        collection_name = os.getenv("COLLECTION_NAME", "jobs")
        info = client.get_collection(collection_name)
        return {
            "status": "success",
            "collection_name": collection_name,
            "total_jobs": info.points_count
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get stats from Qdrant: {str(e)}"}


