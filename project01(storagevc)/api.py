
import asyncio
import sys
from helper.helper import run_pipeline
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from embed_jobs import Search, match_cv_tailor
from shapes.RequestShape import MatchShape

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI()



@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/matches")
def matches(request: MatchShape):
    results = Search(request.query)
    return {
        "query": request.query,
        "results": results,
    }
    


@app.post("/scrape-and-embed")
def scrape_and_embed(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_pipeline)
    return {"message": "Scraping  and embedding pipeline started in background \n scraped jobs will stored to vector database and ready for matching "}

@app.post("/match-cv")
def match_cv_endpoint():
    print("matching candidate cv against all available jobs")
    result = match_cv_tailor()
    return result 