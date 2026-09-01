from pydantic import BaseModel
from typing import Optional


class JobProfile(BaseModel):
    required_skills: list[str]
    preferred_skills: list[str]
    experience_years: Optional[float]
    technologies: list[str]
    responsibilities: list[str]
    seniority: Optional[str]
    domains: list[str]