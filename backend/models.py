from typing import List
from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    summary: str
    missing_keywords: List[str]
    improvement_bullet_points: List[str]
    cover_letter: str


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    model: str
