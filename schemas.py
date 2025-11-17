"""
Database Schemas for Designer Growth Platform

Each Pydantic model maps to a MongoDB collection. The collection name is the
lowercased class name.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

# Core people/entities
class Designer(BaseModel):
    name: str
    email: str
    manager_id: Optional[str] = Field(None, description="Manager user id")
    current_level: str = Field("Junior", description="Career level")
    guilds: List[str] = Field(default_factory=list)

class Manager(BaseModel):
    name: str
    email: str

# Career framework
class Competency(BaseModel):
    key: str = Field(..., description="e.g., product_strategy, craft_quality")
    title: str
    description: Optional[str] = None

class CareerLevel(BaseModel):
    level: str = Field(..., description="Junior, Mid, Senior, Staff, Principal")
    expectations: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of competency key -> expectation summary",
    )

# Skill matrix
class SkillAssessment(BaseModel):
    designer_id: str
    cycle: str = Field(..., description="e.g., 2025-H1")
    ratings: Dict[str, int] = Field(..., description="competency key -> 1..4")
    notes: Optional[str] = None

# Performance reviews
class Review(BaseModel):
    designer_id: str
    cycle: str
    status: str = Field("open", description="open|closed")
    self_eval: Optional[Dict[str, int]] = None
    peer_evals: List[Dict[str, int]] = Field(default_factory=list)
    manager_eval: Optional[Dict[str, int]] = None
    summary: Optional[str] = None

# Goals & development
class Goal(BaseModel):
    designer_id: str
    title: str
    description: Optional[str] = None
    competency_key: Optional[str] = None
    target_date: Optional[datetime] = None
    status: str = Field("not_started", description="not_started|in_progress|done")
    progress: int = Field(0, ge=0, le=100)

# Guilds & mentorship
class Guild(BaseModel):
    name: str
    description: Optional[str] = None
    calendar: List[Dict[str, str]] = Field(default_factory=list, description="list of {date, title}")

class Mentorship(BaseModel):
    mentor_id: str
    mentee_id: str
    start_date: Optional[datetime] = None
    status: str = Field("active", description="active|completed|paused")
    activities: List[Dict[str, str]] = Field(default_factory=list)

# Training resources
class TrainingResource(BaseModel):
    title: str
    url: str
    provider: Optional[str] = None
    tags: List[str] = Field(default_factory=list)  # e.g., ["craft_quality", "leadership"]
    duration_minutes: Optional[int] = None

# Projects and collaboration
class Project(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[str] = None
    designers: List[str] = Field(default_factory=list)
    stages: List[Dict[str, str]] = Field(default_factory=list, description="list of {name, date, notes}")

# Notifications (log only)
class Notification(BaseModel):
    user_id: str
    kind: str = Field(..., description="review_reminder|goal_due|guild_event")
    message: str
    sent_via: List[str] = Field(default_factory=list)  # e.g., ["email", "slack"]

