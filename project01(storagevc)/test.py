from utils import json_serializer
from fetch_LinkedIn_jobs import main as fetch_jobs
import asyncio
from embed_jobs import ingest_jobs
from matching_engine.match_job import match_job
from matching_engine.match_responsibilities import match_responsibilities
import json
from groq_client import generate_job_description, generate_cv_description
from embed_jobs import match_cv_tailor
from model_provider import get_model





def test_responsibilities():
    model = get_model()
    cv_resp = [
                "Designed and developed a secure AI orchestration platform supporting multiple AI providers",
                "Built a 12-layer defense-in-depth security pipeline including WAF, Kong API Gateway, Keycloak JWT authentication, prompt-injection detection, PII detection, and OPA policy checks",
                "Integrated multiple AI providers such as Ollama, OpenAI, and Gemini",
                "Designed an asynchronous orchestration engine with concurrent pre-flight security checks, intent-based routing, and SSE token streaming",
                "Implemented multi-tenancy using PostgreSQL Row-Level Security (RLS)",
                "Added per-tenant quotas and audit logging for metered billing",
                "Containerized and deployed the platform using Docker Compose and Kubernetes",
                "Configured a 4-namespace Kubernetes cluster with NetworkPolicies",
                "Implemented observability using Prometheus, Grafana, and Loki"
            ]
    job_resp = [
        "Analyze, design, and develop business applications.",
        "Gather and evaluate requirements for existing or proposed systems.",
        "Customize and configure existing systems.",
        "Prepare detailed flow charts and diagrams outlining system capabilities and processes.",
        "Perform functional design, internal QA, user acceptance testing, and end-user training.",
        "Select authorized procedures and seek assistance for guideline deviations or unanticipated problems.",
        "Maintain compatibility between systems.",
        "Write and maintain system documentation.",
        "Conduct technical research on system upgrades for feasibility, cost, time, and compatibility.",
        "Test, maintain, and monitor computer programs and systems, including coordinating installations.",
        "Provide staff and users assistance with computer-related problems.",
        "Deploy and maintain containerized applications using Kubernetes."
    ]
    result = match_responsibilities(cv_resp=cv_resp, job_resp=job_resp, model=model)
    with open("responsibilities.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False, default=json_serializer)



def test_job_matching_sorting():
    match_cv_tailor()

def test_job_matching():
    with open("job_profile.json", "r", encoding="utf-8") as f:
        job_profile = json.load(f)
    with open("cv_profile.json", "r", encoding="utf-8") as f:
        cv_profile =  json.load(f)
    result = match_job(job_profile=job_profile, cv_profile=cv_profile)
    print(result)
    
    
async def test_job_ingesting():
        with open("linkedIn_data.json", "r",encoding="utf-8") as f:
            json_data = json.load(f)
            jobs = json_data["data"]
            print(jobs)
        await ingest_jobs(jobs)

    
def test_search_function():
    from embed_jobs import Search, embed_job
    from model_provider import get_model
    from qDrantStore import connect, SearchVector
    
    print("\n--- 1. Testing Search() directly from embed_jobs.py ---")
    try:
        results = Search(query="Python backend", limit=5)
        print("Search() returned:", results)
    except Exception as e:
        print(f"Direct Search() failed with error: {type(e).__name__}: {e}")

    print("\n--- 2. Inspecting raw Qdrant query_points output structure & search relevance ---")
    client = connect()
    model = get_model()
    
    queries = [
            "Miami software engineer"
        ]
    for q in queries:
        print(f"\n{'='*20} Testing Query: '{q}' {'='*20}")
        vec = embed_job(q, model)
        raw = SearchVector(limit=5, client=client, QueryVector=vec)
        
        print(f"Type of raw return from SearchVector: {type(raw)}")
        print(f"Attributes / repr: points count = {len(raw.points) if hasattr(raw, 'points') else 'no points attr'}")
        
        if hasattr(raw, 'points'):
            for idx, pt in enumerate(raw.points, 1):
                payload = pt.payload or {}
                # Check both payload schemas (flat vs nested raw_job/profile)
                raw_job = payload.get("raw_job") if isinstance(payload.get("raw_job"), dict) else payload
                title = raw_job.get("title") or payload.get("title")
                company = raw_job.get("company") or payload.get("company")
                score = pt.score
                print(f"  #{idx} [Cosine Score: {score:.4f}] {title} @ {company}")
                details = raw_job.get("details") or {}
                desc = details.get("description", "")
                if desc:
                    print(f"      Snippet: {desc[:120]}...")

if __name__ == "__main__":
    test_search_function()


