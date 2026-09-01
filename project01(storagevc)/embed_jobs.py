from utils import  json_serializer
import asyncio
from model_provider import get_model
from groq_client import generate_cv_description, generate_tailored_recommendation, generate_job_description, get_groq_client
from utils import getKeywords, boostKeywords, get_spacy_model
import json
from qDrantStore import storeVector, connect, SearchVector
from sentence_transformers import SentenceTransformer
import os 
from dotenv import load_dotenv



def build_job_text(job: dict, job_profile: dict = None):
    job = job or {}
    job_profile = job_profile or {}

    title = job.get("title") or ""
    company = job.get("company") or ""
    location = job.get("location") or ""

    technologies = job_profile.get("technologies") or []
    if isinstance(technologies, list):
        technologies_str = ", ".join(technologies)
    else:
        technologies_str = str(technologies)

    experience_years = job_profile.get("experience_years")
    experience_str = f"{experience_years}" if experience_years is not None else ""
    seniority = job_profile.get("seniority") or ""

    return (
        f"Title: {title}\n"
        f"Company: {company}\n"
        f"Location: {location}\n"
        f"Technologies: {technologies_str}\n"
        f"Experience Years: {experience_str}\n"
        f"Seniority: {seniority}"
    )


def embed_job(job_text: str, model: SentenceTransformer, is_query: bool = False):
    if is_query:
        job_text = "Represent this sentence for searching relevant passages: " + job_text
    return model.encode(job_text)


def main():
    
    client = connect()
    model = get_model()

    with open("linkedIn_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        job_index = 0
        for job in data["data"]:
            job_index += 1
            print(f"Job number: {job_index}")
            job_text = build_job_text(job)
            vector = embed_job(job_text, model)
            storeVector(client, vector=vector, job=job)                  
            print(f"job number: {job_index} embedded and stored")

def Search(query: str = None, limit = 5):
    client = connect()
    model = get_model()
    if query is None:
        query = input("text to seach for in rag: \n")
    
    raw_results = SearchVector(QueryVector=embed_job(query, model,is_query=True), client=client, limit=5)
    

    return [
    {
        "title": result["payload"].get("title"),
        "company": result["payload"].get("company"),
        "location": result["payload"].get("location"),
        "url": result["payload"].get("Job Details URL"),
        "score": result["score"],
        "details": result["payload"].get("details"),
    }
    for result in raw_results
    ]
    


   
async def ingest_jobs(jobs_list:list):
    
    client = connect()
    model = get_model()
    groq_client = get_groq_client()
    
    job_index = 0
    for job in jobs_list:
        job_index += 1
        print(f"Job number: {job_index}")
        job_description = generate_job_description(job=job["details"], client=groq_client).model_dump()
        job_text = build_job_text(job=job, job_profile=job_description)
        payload ={
            "profile": job_description,
            "raw_job": job
        }
        
        vector = embed_job(str(job_text), model)
        storeVector(client, vector=vector, job=payload)                  
        print(f"job number: {job_index} embedded and stored")
        await asyncio.sleep(2.2)


def match_cv_tailor(cv_text: str = None, limit=5):
    if cv_text is None:
        with open("resources/cv.txt", "r", encoding="utf-8") as f:
            cv_text = f.read()





    
    
    client = get_groq_client()
    results = []
    qDrant_client = connect()
    # cv_profile = generate_cv_description(cv_text, client=client).model_dump()
    with open("cv_profile.json", "r", encoding="utf-8") as f:
        cv_profile = json.load(f)
    from matching_engine.match_job import match_job

    
    while True:
        records,offset = qDrant_client.scroll(collection_name=os.getenv("COLLECTION_NAME"), offset=None,with_payload=True,with_vectors=True, limit=60)
        for record in records:
            match_score = match_job(job_profile=record.payload["profile"], cv_profile=cv_profile)
            if(match_score["final_score"] == 0 and not match_score["breakdown"] ):
                continue
            result = {"match_score": match_score, "raw_job":record.payload["raw_job"]}
            results.append(result)

        if offset is None:
            break
    sorted_results = sorted(
                results,
                key=lambda x: x["match_score"]["final_score"],
                reverse=True
            )
    final_results = sorted_results[0:limit]
    with open("match_tailor.json", "w", encoding="utf-8") as f:
        for result in final_results:
            json.dump(result, f, indent=4, ensure_ascii=False, default=json_serializer)
            print(result["raw_job"]["title"])
    
    
    recommendations = generate_tailored_recommendation(cv_text=cv_text, top_matches=final_results)
    with open("final ai rec.txt", "w", encoding="utf-8") as f:
        f.write(recommendations,)
    
    print(f"ai recommendations saved to 'final ai rec.txt' on disk")
    
    """ {
        "final_score": round(final_score, 4),
        "breakdown": {
            "skills": skills_score,
            "responsibilities": responsibilities_score,
            "experience": experience_score,
            "seniority": seniority_score
        }"""







if __name__ == "__main__":
    match_cv_tailor()