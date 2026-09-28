import sys
import asyncio
from fetch_LinkedIn_jobs import main as scrape_jobs
from embed_jobs import ingest_jobs


def scrape_worker(keywords: str = "junior software engineer", location: str = "United States"):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(scrape_jobs(keywords=keywords, location=location))
    except Exception as E:
        print(f"error occured: {E}")
    finally:
        loop.close()
        
        
async def run_pipeline(
    keywords:str= "junior software developper",
    location: str = "united states"
):
    jobs = await asyncio.to_thread(scrape_worker, keywords, location)
    
    # Guard clause: stop if scraping failed or returned nothing
    if jobs is None:
        print("Pipeline aborted because scraping failed.")
        return

    await ingest_jobs(jobs)
    


