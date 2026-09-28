from typing import Optional
from pydantic import BaseModel


class JobFilters(BaseModel):
    location: Optional[str] = None
    remote: Optional[bool] = None
    seniority: Optional[str] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    visa_sponsorship: Optional[bool] = None
    clearance_required: Optional[bool] = None
    max_age_days: Optional[int] = None
