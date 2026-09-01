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



    
    
    
    
class CandidateShape(BaseModel):
    target_roles: list[str]
    skills: list[str]
    experience_years: float | None
    experience: list[Experience]
    education: list[Education]
    certifications: list[str]
    seniority: str
    

