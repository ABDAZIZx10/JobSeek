from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SeniorityLevel(str, Enum):
    ENTRY_LEVEL = "entry level"
    JUNIOR = "junior"
    MID = "mid"
    MID_SENIOR = "mid-senior level"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"


class JobProfile(BaseModel):
    required_skills: list[str]
    preferred_skills: list[str]
    experience_years: Optional[float] = None
    technologies: list[str]
    responsibilities: list[str]
    seniority: Optional[SeniorityLevel] = None
    domains: list[str]
    role_aliases: list[str]