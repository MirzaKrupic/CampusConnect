"""
Group endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List

from backend.models.group import GroupCreate, GroupResponse, GroupSummary, JoinGroupRequest
from backend.services.group_service import group_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(group_data: GroupCreate) -> Dict[str, Any]:
    """
    Create a new study group
    - Writes to PostgreSQL (source of truth)
    - Creates node in Neo4j (for recommendations)
    - Caches summary in Redis
    """
    try:
        group = await group_service.create_group(
            name=group_data.name, course_code=group_data.course_code
        )
        return group
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{group_id}", response_model=GroupSummary)
async def get_group(group_id: int) -> Dict[str, Any]:
    """
    Get group details
    - Tries Redis cache first
    - Falls back to PostgreSQL
    - Enriches with member count and post count
    """
    group = await group_service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.post("/{group_id}/join")
async def join_group(group_id: int, request: JoinGroupRequest) -> Dict[str, Any]:
    """
    Join a study group
    - Writes membership to PostgreSQL
    - Creates MEMBER_OF relationship in Neo4j
    - Pushes activity to Redis stream
    - Invalidates group cache
    - Awards participation points
    """
    try:
        result = await group_service.join_group(
            user_id=request.user_id, group_id=group_id, role=request.role
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{group_id}/members")
async def get_group_members(group_id: int) -> List[Dict[str, Any]]:
    """Get all members of a group from PostgreSQL"""
    members = await group_service.get_group_members(group_id)
    return members


@router.get("/{group_id}/activity")
async def get_group_activity(group_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent activity for a group
    - Reads from Redis LIST (fast, in-memory)
    - Returns last N activities
    """
    activities = await group_service.get_recent_activity(group_id, limit)
    return activities
