"""
User Service - Coordinates user operations across multiple databases
Demonstrates polyglot persistence pattern for user data
"""
import logging
from typing import Optional, Dict, Any

from backend.db.postgres import postgres_client
from backend.db.redis import redis_client
from backend.db.neo4j import neo4j_client

logger = logging.getLogger(__name__)


class UserService:
    """
    Orchestrates user operations across:
    - PostgreSQL: authoritative user data
    - Neo4j: user nodes for graph relationships
    - Redis: cached user profiles
    """

    async def create_user(self, email: str, full_name: str) -> Dict[str, Any]:
        """
        Create user in PostgreSQL, mirror to Neo4j, cache in Redis
        Demonstrates write propagation across multiple DBs
        """
        # 1. Create in PostgreSQL (source of truth)
        user = await postgres_client.create_user(email, full_name)
        logger.info(f"Created user {user['id']} in PostgreSQL")

        # 2. Create corresponding node in Neo4j for relationship queries
        await neo4j_client.create_user_node(
            user_id=user["id"], email=user["email"], full_name=user["full_name"]
        )
        logger.info(f"Created user node {user['id']} in Neo4j")

        # 3. Cache profile in Redis
        await redis_client.cache_user(user["id"], user)
        logger.info(f"Cached user {user['id']} in Redis")

        return user

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user with cache-aside pattern:
        1. Try Redis cache first (fast)
        2. Fallback to PostgreSQL (authoritative)
        3. Repopulate cache on miss
        """
        # Try cache first
        cached_user = await redis_client.get_cached_user(user_id)
        if cached_user:
            logger.info(f"Cache hit for user {user_id}")
            return cached_user

        # Cache miss - get from PostgreSQL
        logger.info(f"Cache miss for user {user_id}, fetching from PostgreSQL")
        user = await postgres_client.get_user(user_id)

        if user:
            # Repopulate cache
            await redis_client.cache_user(user_id, user)

        return user

    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get enriched user profile:
        - Basic data from PostgreSQL
        - Friend count from Neo4j graph degree
        - Group memberships from PostgreSQL
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        # Enrich with graph data
        friend_count = await neo4j_client.get_user_degree(user_id)
        groups = await postgres_client.get_user_groups(user_id)

        profile = {
            **user,
            "friend_count": friend_count,
            "group_count": len(groups),
            "groups": groups,
        }

        return profile

    async def add_friend(self, user1_id: int, user2_id: int) -> Dict[str, Any]:
        """
        Create friendship relationship in Neo4j graph
        This is purely a graph operation - no PostgreSQL involvement
        """
        # Verify both users exist in PostgreSQL
        user1 = await postgres_client.get_user(user1_id)
        user2 = await postgres_client.get_user(user2_id)

        if not user1 or not user2:
            raise ValueError("One or both users do not exist")

        # Check if already friends
        are_friends = await neo4j_client.are_friends(user1_id, user2_id)
        if are_friends:
            raise ValueError("Users are already friends")

        # Create friendship in Neo4j
        await neo4j_client.create_friendship(user1_id, user2_id)
        logger.info(f"Created friendship: {user1_id} <-> {user2_id}")

        # Invalidate user caches since friend_count changed
        await redis_client.invalidate_user_cache(user1_id)
        await redis_client.invalidate_user_cache(user2_id)

        return {
            "user1_id": user1_id,
            "user2_id": user2_id,
            "status": "friends",
        }


# Global instance
user_service = UserService()
