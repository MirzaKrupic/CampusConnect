"""
Post-related Pydantic models
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any


class PostCreate(BaseModel):
    author_id: int
    type: str  # "resource", "question", "note"
    title: str
    body: str
    tags: List[str] = []
    attachments: List[Dict[str, Any]] = []


class PostResponse(BaseModel):
    id: str
    author_id: int
    group_id: int
    type: str
    title: str
    body: str
    tags: List[str]
    attachments: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class PostWithAuthor(PostResponse):
    author_name: str
    author_email: str
    group_name: Optional[str] = None


class CommentCreate(BaseModel):
    author_id: int
    body: str


class CommentResponse(BaseModel):
    id: str
    post_id: str
    author_id: int
    body: str
    created_at: datetime


class LeaderboardEntry(BaseModel):
    user_id: int
    full_name: Optional[str] = None
    points: int
    rank: Optional[int] = None
