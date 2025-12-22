"""
User-related Pydantic models
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime
    friend_count: Optional[int] = 0
    group_count: Optional[int] = 0


class FriendRecommendation(BaseModel):
    user_id: int
    full_name: str
    email: str
    mutual_friends: int
    reason: str
