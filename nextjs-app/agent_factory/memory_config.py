"""Memory configuration classes for Agent Factory V1."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """Configuration for agent memory system."""
    
    enabled: bool = True
    conversation_max_messages: int = 20
    summarize_after: int = 15
    user_profile_enabled: bool = True
    goals_tracking_enabled: bool = True
    max_goals: int = 5


class UserProfile(BaseModel):
    """User profile information stored in memory."""
    
    name: Optional[str] = None
    role: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    communication_style: Optional[str] = None


class Goal(BaseModel):
    """Goal tracking for user objectives."""
    
    description: str
    status: str = "active"
    created_date: datetime = Field(default_factory=datetime.now)
    notes: List[str] = Field(default_factory=list) 