"""
Recommendation endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from backend.models.user import FriendRecommendation
from backend.models.group import GroupRecommendation
from backend.models.post import LeaderboardEntry
from backend.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/users/{user_id}/friends", response_model=List[FriendRecommendation])
async def recommend_friends(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Recommend friends based on friend-of-friend graph traversal

    WHY NEO4J:
    SQL equivalent would require complex self-joins:
    ```sql
    SELECT u3.*, COUNT(DISTINCT u2.id) as mutual_friends
    FROM users u1
    JOIN friendships f1 ON u1.id = f1.user1_id
    JOIN users u2 ON f1.user2_id = u2.id
    JOIN friendships f2 ON u2.id = f2.user1_id
    JOIN users u3 ON f2.user2_id = u3.id
    LEFT JOIN friendships f3 ON (u1.id = f3.user1_id AND u3.id = f3.user2_id)
    WHERE u1.id = ? AND u3.id != ? AND f3.id IS NULL
    GROUP BY u3.id
    ORDER BY mutual_friends DESC
    LIMIT 10
    ```

    Neo4j Cypher is much clearer:
    ```cypher
    MATCH (me)-[:FRIEND]->(friend)-[:FRIEND]->(fof)
    WHERE me <> fof AND NOT (me)-[:FRIEND]->(fof)
    RETURN fof, COUNT(friend) as mutual_friends
    ORDER BY mutual_friends DESC
    LIMIT 10
    ```
    """
    recommendations = await recommendation_service.recommend_friends(user_id, limit)
    return recommendations


@router.get("/users/{user_id}/groups", response_model=List[GroupRecommendation])
async def recommend_groups(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Recommend groups based on friend network

    Uses Neo4j to find groups where user's friends are members
    Much simpler than SQL multi-join equivalent
    """
    recommendations = await recommendation_service.recommend_groups(user_id, limit)
    return recommendations


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get participation leaderboard

    WHY REDIS:
    - Redis sorted sets (ZSET) are O(log N) for updates and range queries
    - PostgreSQL would need ORDER BY with LIMIT, scanning full table
    - For real-time leaderboards with frequent updates, Redis is much faster

    Redis:
    - ZINCRBY: O(log N)
    - ZREVRANGE: O(log N + M) where M is number of results

    PostgreSQL:
    - UPDATE + ORDER BY + LIMIT: O(N log N) where N is total users
    """
    leaderboard = await recommendation_service.get_leaderboard(limit)
    return leaderboard
