"""
Post endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from backend.models.post import PostCreate, PostWithAuthor
from backend.services.post_service import post_service

router = APIRouter(prefix="/groups/{group_id}/posts", tags=["posts"])


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_post(group_id: int, post_data: PostCreate) -> Dict[str, Any]:
    """
    Create a post in a group
    - Stores flexible document in MongoDB
    - Adds to Redis hot posts (sorted set)
    - Pushes activity to Redis stream
    - Awards points to author
    - Invalidates group cache
    """
    try:
        post = await post_service.create_post(
            author_id=post_data.author_id,
            group_id=group_id,
            post_type=post_data.type,
            title=post_data.title,
            body=post_data.body,
            tags=post_data.tags,
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feed", response_model=List[PostWithAuthor])
async def get_group_feed(group_id: int, limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
    """
    Get feed for a group
    - Reads posts from MongoDB
    - Enriches with author data from PostgreSQL (via Redis cache)
    - Enriches with group data from PostgreSQL (via Redis cache)

    Demonstrates cross-database query enrichment
    """
    posts = await post_service.get_group_feed(group_id, limit, skip)
    return posts
