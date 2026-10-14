# backend/app/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field

class Project(BaseModel):
    title: str
    description: str
    technologies: List[str]

class Experience(BaseModel):
    role: str
    company: str
    duration: Optional[str] = None
    highlights: List[str]

class StructuredProfile(BaseModel):
    skills: List[str]
    experiences: List[Experience]
    projects: List[Project]

class ResumeAnalysisResponse(BaseModel):
    company: str
    job_role: str
    profile: StructuredProfile
    fit_score: int = Field(..., ge=0, le=100)
    matched_keywords: List[str]
    missing_keywords: List[str]
    suggestions: List[str]
    likely_questions: List[str]