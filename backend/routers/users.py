"""
User endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from backend.models.user import UserCreate, UserResponse, UserProfile
from backend.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate) -> Dict[str, Any]:
    """
    Create a new user
    - Writes to PostgreSQL (source of truth)
    - Creates node in Neo4j (for graph relationships)
    - Caches in Redis (for fast access)
    """
    try:
        user = await user_service.create_user(
            email=user_data.email, full_name=user_data.full_name
        )
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(user_id: int) -> Dict[str, Any]:
    """
    Get user profile
    - Tries Redis cache first (fast path)
    - Falls back to PostgreSQL on cache miss
    - Enriches with friend count from Neo4j
    """
    user = await user_service.get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/{user_id}/friends/{friend_id}")
async def add_friend(user_id: int, friend_id: int) -> Dict[str, Any]:
    """
    Add a friend relationship
    - Creates bidirectional FRIEND relationship in Neo4j
    - Invalidates Redis cache for both users
    - No PostgreSQL write (relationships live in graph DB)
    """
    try:
        result = await user_service.add_friend(user_id, friend_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
