from model_provider import get_sparse_model
from utils import  json_serializer
import asyncio
from model_provider import get_model
from groq_client import generate_cv_description, generate_tailored_recommendation, generate_job_description, get_groq_client,extract_job_filters
from utils import getKeywords, boostKeywords, get_spacy_model
import json
from qDrantStore import storeVector, connect, SearchVector, build_qdrant_filter
from qdrant_client.models import SparseVector
from sentence_transformers import SentenceTransformer
import os 
from dotenv import load_dotenv



def build_job_text(job: dict, job_profile: dict = None):
    job = job or {}
    job_profile = job_profile or {}

    title = job.get("title") or ""
    company = job.get("company") or ""
    location = job.get("location") or ""
    role_aliases = job_profile.get("role_aliases") or []
    if isinstance(role_aliases, list):
        role_aliases_str = ", ".join(role_aliases)
    else:
        role_aliases_str = str(role_aliases)
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
        f"Role Aliases: {role_aliases_str}\n"
        f"Technologies: {technologies_str}\n"
        f"Experience Years: {experience_str}\n"
        f"Seniority: {seniority}"
    )


def embed_job(job_text: str, model: SentenceTransformer, is_query: bool = False):
    if is_query:
        job_text = "Represent this sentence for searching relevant passages: " + job_text
    return model.encode(job_text)

def sparse_embedding(sparse_model,job_text):
    vector = list(sparse_model.embed([job_text]))[0]
    return SparseVector(
        indices=vector.indices.tolist(),
        values=vector.values.tolist()
    )


def Search(query: str = None, limit=5):
    client = connect()

    groq_client = get_groq_client()
    dense_model = get_model()
    sparse_model = get_sparse_model()

    if query is None:
        query = input("text to search for in rag:\n")

    # 1. Extract hard filters
    filters = extract_job_filters(
        query,
        client=groq_client
    )
    active_filters = {
        key: value
        for key, value in filters.model_dump().items()
        if value is not None
    }
    print(f"filters: {active_filters or 'none'}")
    query_filter = build_qdrant_filter(filters)

    # 2. Create dense query vector
    dense_vector = embed_job(
        query,
        dense_model,
        is_query=True
    )

    # 3. Create sparse query vector
    sparse_vector = sparse_embedding(
        sparse_model,
        query
    )

    # 4. Hybrid search
    raw_results = SearchVector(
        client=client,
        dense_vector=dense_vector,
        sparse_vector=sparse_vector,
        limit=limit,
        query_filter=query_filter
    )

    return [
        {
            "title": result.payload["raw_job"].get("title"),
            "company": result.payload["raw_job"].get("company"),
            "location": result.payload["raw_job"].get("location"),
            "url": result.payload["raw_job"].get("Job Details URL"),
            "score": result.score,
            "details": result.payload["raw_job"].get("details"),
        }
        for result in raw_results.points
    ]

    


   
async def ingest_jobs(jobs_list:list):
    
    client = connect()
    model = get_model()
    sparse_model = get_sparse_model()
    groq_client = get_groq_client()
    
    job_index = 0
    for job in jobs_list:
        job_index += 1
        print(f"Job number: {job_index}")
        job_description = generate_job_description(job, client=groq_client).model_dump()
        job_text = build_job_text(job=job, job_profile=job_description)
        job_filters = extract_job_filters(job, client=groq_client).model_dump()
        payload ={
            "profile": job_description,
            "raw_job": job,
            "job_filters": job_filters
        }
        
        dense_vector = embed_job(str(job_text), model)
        sparse_text = f"""
                    Title: {job["title"]}
                    Technologies: {", ".join(job_description["technologies"])}
                    Role: {", ".join(job_description["role_aliases"])}
                    Description: {job["details"]["description"]}
                        """

        sparse_vector = sparse_embedding(sparse_model=sparse_model,job_text=sparse_text)
        storeVector(client, vector={"dense": dense_vector, "sparse": sparse_vector}, job=payload)                  
        if jobs_list.index(job) == len(jobs_list) - 1 :
            print(f"job number: {job_index} embedded and stored")
            print("waiting for 30 seconds since llm usage is heavy  to avoid hitting (8000) TPM limit ")
            await asyncio.sleep(30)


def match_cv_tailor(cv_text: str = None, limit=5):
    if cv_text is None:
        with open("resources/cv.txt", "r", encoding="utf-8") as f:
            cv_text = f.read()





    
    
    client = get_groq_client()
    results = []
    qDrant_client = connect()
    cv_profile = generate_cv_description(cv_text, client=client).model_dump()
    with open("cv_profile.json", "w", encoding="utf-8") as f:
        json.dump(cv_profile, f, indent=4, ensure_ascii=False)
    # with open("cv_profile.json", "r", encoding="utf-8") as f:
    #     cv_profile = json.load(f)
    from matching_engine.match_job import match_job

    
    offset = None
    while True:
        records,offset = qDrant_client.scroll(collection_name=os.getenv("COLLECTION_NAME"), offset=offset,with_payload=True,with_vectors=False, limit=60)
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
        json.dump(final_results, f, indent=4, ensure_ascii=False, default=json_serializer)

    recommendations = generate_tailored_recommendation(
        cv_text=cv_text,
        top_matches=final_results,
    )

    with open("final ai rec.txt", "w", encoding="utf-8") as f:
        f.write(recommendations)

    return {
        "matches": final_results,
        "recommendations": recommendations,
    }







if __name__ == "__main__":
    sparse = get_sparse_model()
    result = sparse_embedding(sparse, input("shit to embed sparse :\n"))
    print(type(result))