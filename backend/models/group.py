"""
Group-related Pydantic models
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class GroupCreate(BaseModel):
    name: str
    course_code: str


class GroupResponse(BaseModel):
    id: int
    name: str
    course_code: str
    created_at: datetime


class GroupSummary(BaseModel):
    id: int
    name: str
    course_code: str
    created_at: datetime
    member_count: Optional[int] = 0
    post_count: Optional[int] = 0


class JoinGroupRequest(BaseModel):
    user_id: int
    role: str = "member"


class GroupRecommendation(BaseModel):
    group_id: int
    name: str
    course_code: str
    friend_count: int
    reason: str
