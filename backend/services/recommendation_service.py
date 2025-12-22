"""
Recommendation Service - Graph-based recommendations via Neo4j
"""
import logging
from typing import List, Dict, Any

from backend.db.neo4j import neo4j_client
from backend.db.postgres import postgres_client

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Uses Neo4j graph database for social recommendations
    Demonstrates why graph databases excel at relationship queries
    """

    async def recommend_friends(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Friend-of-friend recommendations from Neo4j

        This query would be extremely complex in SQL:
        - Multiple self-joins on users table
        - Subqueries to exclude existing friends
        - Complex aggregation for mutual friend counts

        In Neo4j it's a simple graph traversal pattern
        """
        recommendations = await neo4j_client.recommend_friends(user_id, limit)
        logger.info(f"Found {len(recommendations)} friend recommendations for user {user_id}")
        return recommendations

    async def recommend_groups(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Group recommendations based on friend network

        SQL equivalent would require:
        - Join users -> friendships -> users -> group_memberships -> groups
        - Filtering out user's existing groups
        - Aggregating friend counts

        Neo4j handles this naturally with relationship traversal
        """
        recommendations = await neo4j_client.recommend_groups(user_id, limit)
        logger.info(f"Found {len(recommendations)} group recommendations for user {user_id}")
        return recommendations

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get participation leaderboard from Redis
        Enrich with user data from PostgreSQL

        Demonstrates Redis sorted sets for leaderboard use case
        Much faster than SQL ORDER BY with LIMIT
        """
        from backend.db.redis import redis_client

        # Get top scorers from Redis (O(log N) operation)
        leaderboard = await redis_client.get_leaderboard(limit)

        # Enrich with user data from PostgreSQL
        enriched = []
        for idx, entry in enumerate(leaderboard):
            user = await postgres_client.get_user(entry["user_id"])
            enriched.append(
                {
                    "rank": idx + 1,
                    "user_id": entry["user_id"],
                    "full_name": user["full_name"] if user else "Unknown",
                    "points": entry["points"],
                }
            )

        return enriched

    async def get_common_groups(
        self, user1_id: int, user2_id: int
    ) -> List[Dict[str, Any]]:
        """
        Find common groups between two users
        Graph query is much simpler than SQL JOIN equivalent
        """
        return await neo4j_client.get_common_groups(user1_id, user2_id)


# Global instance
recommendation_service = RecommendationService()
