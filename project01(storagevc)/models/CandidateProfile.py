from pydantic import BaseModel

class Experience(BaseModel):
    title: str
    company: str | None
    duration_months: int | None
    technologies: list[str]
    responsibilities: list[str]
    domains: list[str]
class Education(BaseModel):
    degree: str
    field: str | None
    institution: str | None
    start_year: int | None
    end_year: int | None



    
    
class Project(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = []
    
class CandidateShape(BaseModel):
    target_roles: list[str] 
    skills: list[str]
    experience_years: float | None
    experience: list[Experience]
    education: list[Education] | None
    certifications: list[str] | None
    seniority: str | None
    full_name: str | None = None
    location: str | None = None
    languages: list[str] | None = None
    summary: str | None = None          # 1–2 sentence headline, not the whole CV
    projects: list[Project] | None = None
    github: str | None = None
    linkedin: str | None = None

    

