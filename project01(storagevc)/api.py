
import asyncio
import sys
from helper.helper import run_pipeline
from fastapi import FastAPI, BackgroundTasks, File, Form, UploadFile
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
async def match_cv_endpoint(
    file: UploadFile = File(...),
    limit: int = Form(5)
    ):
    raw_bytes = await file.read()
    cv_text = raw_bytes.decode("utf-8")
    result = match_cv_tailor(
        cv_text=cv_text,
        limit=limit   
    )
    return result 