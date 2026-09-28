from pydantic import BaseModel


class MatchShape(BaseModel):
    
    query: str


class MatchCvShape(BaseModel):
    cv_text: str
    limit: int = 5