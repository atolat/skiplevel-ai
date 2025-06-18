"""Data models for employee profiles."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import date, datetime

@dataclass
class EmployeeProfile:
    """Employee profile data model."""
    id: str
    email: str
    name: str
    title: str
    specialization: str
    level: Optional[str] = None
    team: Optional[str] = None
    years_experience: Optional[int] = None
    years_at_company: Optional[int] = None
    tech_skills: Optional[List[str]] = None
    current_projects: Optional[List[str]] = None
    career_goals: Optional[List[str]] = None
    biggest_challenges: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    learning_goals: Optional[List[str]] = None
    
    # Last human manager assessment
    last_review_date: Optional[date] = None
    last_review_rating: Optional[str] = None
    last_review_feedback: Optional[str] = None
    last_reviewer: Optional[str] = None
    
    # AI management preferences
    communication_style: Optional[str] = None
    feedback_frequency: Optional[str] = None
    meeting_style: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    profile_completed: bool = False 