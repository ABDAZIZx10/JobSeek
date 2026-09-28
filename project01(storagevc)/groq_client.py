import json
from models.CandidateProfile import CandidateShape
from models.JobProfile import JobProfile
from models.jobfilters import JobFilters
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
        model=os.getenv("GENERATION_MODEL"),
        messages=[
            {"role": "system", "content": f"{os.getenv('SYSTEM_PROMPT_RANKING', '')}"},
            {"role":"user", "content": prompt}
        ],
        temperature= 0.2,
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()

def generate_tailored_recommendation(cv_text: str, top_matches:list) -> list:
    client = get_groq_client()
    jobs_summary = ""
    for idx, match in enumerate(top_matches, 1):
        job = match.get("raw_job")
        jobs_summary += f"\n--- Job #{idx}: {job.get('title')} at {job.get('company')} (more details about the job at '{job.get('Job Details URL')}') ---\n"
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
        2. 2-3 "Tailored CV Bullets" rewritten to target this specific job's requirements, your claims must be supported by the cv .
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
        max_tokens=4096
    )

    print(f"total tokens used for recommendation: {response.usage.total_tokens}")
    return response.choices[0].message.content


def generate_job_description(job: dict, client:Groq):

    job_for_groq = {
    "title": job.get("title"),
    "details": {
        "description": job.get("details", {}).get("description"),
        "Seniority level": job.get("details", {}).get("Seniority level"),
        "Job function": job.get("details", {}).get("Job function"),
        "Industries": job.get("details", {}).get("Industries"),
    }
}

    
    prompt = f"""You are a structured information extraction component.

            Your ONLY task is to extract information from the provided job posting.

            Rules:
            - Do Not Leave the responsibilities field empty even if is unclear, in case of any confusion  generate  from the general context of the job posting
            - The responsibilities field should not be a huge blob a responsibility should short  and clear , seperate every long and complex responsibility into short and clear one  
            -For experience ranges, return the maximum number of years.For example, "0–2 years" -> 2.
            -Input for seniority should be 'entry level', 'junior', 'mid', 'mid-senior level', 'senior', 'lead', 'manager' or 'director' 
            - Return ONLY the requested JSON object.
            - Do not explain your answer.
            - Do not add fields.
            - Do not add notes.
            - Do not infer information.
            - Do not use external knowledge.
            - If information is missing, return null.
            - If a list has no items, return [].
            - Only include technologies explicitly mentioned.
            - Separate required and preferred information. \n here is the job details {job_for_groq}"""
    
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
        },
        max_tokens=4096
    )
    result =  response.choices[0].message.content  
    print("(job description)  total  tokens used:", response.usage.total_tokens)
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
        },
        max_tokens=4096
    )
    result =  response.choices[0].message.content  
    cv_profile = CandidateShape.model_validate_json(result)
    return cv_profile

def extract_job_filters(query: str, client: Groq) -> JobFilters:
    prompt = f"""
    Extract hard constraints from the following job search query.

    Hard constraints include:
    - location
    - remote status
    - seniority
    - minimum/maximum salary
    - visa sponsorship
    - security clearance
    - maximum job age

    Do NOT include skills, technologies, job titles, domains, or responsibilities
    in the filters. Those belong to the semantic query.

    If a constraint is not explicitly stated, return null.
    Return ONLY the requested JSON object.

    User query:
    {query}
    """

    response = client.chat.completions.create(
        model=os.getenv("GENERATION_MODEL"),
        messages=[
            {
                "role": "system",
                "content": """
                You are a structured job-search query extraction component.
                Extract only explicit hard constraints.
                Never infer missing constraints.
                Return only data matching the provided JSON schema.
                """
            },
            {"role": "user", "content": prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "job_filters",
                "schema": JobFilters.model_json_schema()
            }
        },
        temperature=0,
        max_tokens=4096
    )

    result = response.choices[0].message.content
    print("(filters generation) total  tokens used:", response.usage.total_tokens)
    return JobFilters.model_validate_json(result)
