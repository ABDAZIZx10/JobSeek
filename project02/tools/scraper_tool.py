import asyncio
import settings
from helper.helper import run_pipeline

def scrape_jobs(
    keywords:str ="junior software developper",
    location:str = "United States"
):
    """Runs the scraping & ingestion pipeline."""
    try:
        asyncio.run(run_pipeline(keywords=keywords,location=location))
        return {"status": "success", "message": "Scraping and ingestion completed."}
    except Exception as e:
        return {"status": "error", "message": f"Scraping pipeline failed: {str(e)}"}
