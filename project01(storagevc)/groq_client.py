import json
from models.CandidateProfile import CandidateShape
from models.JobProfile import JobProfile
from dotenv import load_dotenv
import os 
from groq import Groq
load_dotenv()
def get_groq_client():
    
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_cv_summary(cv_text: str) -> str:
    client = get_groq_client()
    prompt = f"""
    Given the following CV, extract a concise summary focusing strictly on:
    1. Target job title / primary role
    2. Core programming languages, frameworks, and databases
    3. Key technical domain expertise (e.g., Web Scraping, Vector DBs, RAG, Automation)
    4. experience
    Do NOT include education, soft skills, or introductory fluff. Output ONLY the dense summary text.
    CV Content:
    {cv_text}
    """
    
    response = client.chat.completions.create(
        model=os,
        messages=[
            {"role": "system", "content": f"{os.getenv("SYSTEM_PROMPT")}"},
            {"role":"user", "content": prompt}
        ],
        temperature= 0.2,
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

def generate_tailored_recommendation(cv_text: str, top_matches:list) -> list:
    client = get_groq_client()
    jobs_summary = ""
    for idx, match in enumerate(top_matches, 1):
        job = match.get("raw_job")
        jobs_summary += f"\n--- Job #{idx}: {job.get("title")} at {job.get("company")} (more details about the job at '{job.get("Job Details URL")}') ---\n"
        print(jobs_summary)
        details = job.get("details") or {}
        jobs_summary += f"Description: {details.get('description', 'N/A')}\n"
        
    prompt = f"""
        Candidate Full CV:
        {cv_text}
        Top Matched Job Listings:
        {jobs_summary}
        Task:
        For each job listing, provide:
        1. A brief "Match Reason" (why candidate fits this role).
        2. 2-3 "Tailored CV Bullets" rewritten to target this specific job's requirements.
        3. keep your tone throughout this response like you are jarvis from the famous movie character iron man from marvel
        4. dont make your answer too long and dont give a very short answer either 
        5. after stating why the job matches you should inform the user with enough details from the job to give the user more context about the job 
        6. also provide a link that will take the user to the job details page 
            """
    
    response = client.chat.completions.create(
        model=os.getenv("GENERATION_MODEL"),
        messages=[
            {"role": "system", "content": "You are an expert AI Career Coach & Resume Consultant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    print(f"total tokens used for recommendation: {response.usage.total_tokens}")
    return response.choices[0].message.content


def generate_job_description(job: dict, client:Groq):
    from embed_jobs import build_job_text
    job_description = build_job_text(job)
    prompt = f"""You are a structured information extraction component.

            Your ONLY task is to extract information from the provided job posting.

            Rules:
            - Do Not Leave the responsibilities field empty even if is unclear, in case of any confusion  generate  from the general context of the job posting
            - The responsibilities field should not be a huge blob a responsibility should short  and clear , seperate every long and complex responsibility into short and clear one  
            - Return ONLY the requested JSON object.
            - Do not explain your answer.
            - Do not add fields.
            - Do not add notes.
            - Do not infer information.
            - Do not use external knowledge.
            - If information is missing, return null.
            - If a list has no items, return [].
            - Only include technologies explicitly mentioned.
            - Separate required and preferred information. \n here is the job details {job_description}"""
    
    response = client.chat.completions.create(
        model=os.getenv("GENERATION_MODEL"),
        messages=[
            {"role": "system", "content": """
            You are a structured job information extraction component.
            Return only the data required by the provided JSON schema.
            Never explain, comment, infer, or add information.
            """},
            {"role": "user", "content": prompt}
        ],
        response_format={
            "type":"json_schema",
            "json_schema": {
                "name": "job_profile", 
                "schema" : JobProfile.model_json_schema()
                }
        }
    )
    result =  response.choices[0].message.content  
    print("total  tokens used:", response.usage.total_tokens)
    job_profile = JobProfile.model_validate_json(result)
    return job_profile 




def generate_cv_description(cv:str,client:Groq):
    if cv == None:
        with open("resources/cv.txt", "r", encoding="utf-8") as f:
            cv = f.read()    
    prompt = f"""You are a structured information extraction component.

            Your ONLY task is to extract information from the provided cv .

            Rules:
            - Do Not Leave the target_roles field empty even if is unclear, in case of any confusion just generate the roles this cv can apply for  from the general context of the cv  
            - Return ONLY the requested JSON object.
            - Do not explain your answer.
            - Do not add fields.
            - Do not add notes.
            - Do not infer information.
            - Do not use external knowledge.
            - If information is missing, return null.
            - If a list has no items, return [].
            - Only include technologies explicitly mentioned.
            - Separate required and preferred information. \n here is the cv details {cv}"""
    
    response = client.chat.completions.create(
        model=os.getenv("GENERATION_MODEL"),
        messages=[
            {"role": "system", "content": """
            You are a structured job information extraction component.
            Return only the data required by the provided JSON schema.
            Never explain, comment, infer, or add information.
            """},
            {"role": "user", "content": prompt}
        ],
        response_format={
            "type":"json_schema",
            "json_schema": {
                "name": "job_profile", 
                "schema" : CandidateShape.model_json_schema()
                }
        }
    )
    result =  response.choices[0].message.content  
    cv_profile = CandidateShape.model_validate_json(result)
    return cv_profile