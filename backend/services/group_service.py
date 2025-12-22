"""
Group Service - Coordinates group operations across databases
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from backend.db.postgres import postgres_client
from backend.db.redis import redis_client
from backend.db.neo4j import neo4j_client
from backend.db.mongo import mongo_client

logger = logging.getLogger(__name__)


class GroupService:
    """
    Orchestrates group operations across:
    - PostgreSQL: authoritative group data and memberships
    - Neo4j: group nodes and MEMBER_OF relationships
    - Redis: cached group summaries and activity streams
    - MongoDB: post counts
    """

    async def create_group(self, name: str, course_code: str) -> Dict[str, Any]:
        """
        Create group in PostgreSQL, mirror to Neo4j, cache summary in Redis
        """
        # 1. Create in PostgreSQL
        group = await postgres_client.create_group(name, course_code)
        logger.info(f"Created group {group['id']} in PostgreSQL")

        # 2. Create node in Neo4j for graph queries
        await neo4j_client.create_group_node(
            group_id=group["id"], name=group["name"], course_code=group["course_code"]
        )
        logger.info(f"Created group node {group['id']} in Neo4j")

        # 3. Cache in Redis
        group_summary = {**group, "member_count": 0, "post_count": 0}
        await redis_client.cache_group(group["id"], group_summary)

        return group

    async def get_group(self, group_id: int) -> Dict[str, Any]:
        """
        Get group with cache-aside pattern + enrichment
        """
        # Try cache first
        cached_group = await redis_client.get_cached_group(group_id)
        if cached_group:
            logger.info(f"Cache hit for group {group_id}")
            return cached_group

        # Cache miss - get from PostgreSQL and enrich
        logger.info(f"Cache miss for group {group_id}, fetching from PostgreSQL")
        group = await postgres_client.get_group(group_id)

        if not group:
            return None

        # Enrich with counts
        members = await postgres_client.get_group_members(group_id)
        post_count = await mongo_client.get_post_count(group_id)

        group_summary = {
            **group,
            "member_count": len(members),
            "post_count": post_count,
        }

        # Cache the enriched data
        await redis_client.cache_group(group_id, group_summary)

        return group_summary

    async def join_group(
        self, user_id: int, group_id: int, role: str = "member"
    ) -> Dict[str, Any]:
        """
        Add user to group - demonstrates coordinated write across 3 DBs:
        1. PostgreSQL: membership record
        2. Neo4j: MEMBER_OF relationship
        3. Redis: activity stream + cache invalidation
        """
        # 1. Add membership in PostgreSQL
        membership = await postgres_client.add_membership(user_id, group_id, role)
        logger.info(f"Added user {user_id} to group {group_id} in PostgreSQL")

        # 2. Create MEMBER_OF relationship in Neo4j
        await neo4j_client.create_membership(user_id, group_id, role)
        logger.info(f"Created MEMBER_OF relationship in Neo4j")

        # 3. Push activity to Redis stream
        activity = {
            "type": "join",
            "user_id": user_id,
            "group_id": group_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await redis_client.push_activity(group_id, activity)
        logger.info(f"Pushed join activity to Redis stream for group {group_id}")

        # 4. Invalidate group cache (member_count changed)
        await redis_client.invalidate_group_cache(group_id)

        # 5. Award points for participation
        await redis_client.increment_user_points(user_id, points=5)

        return membership

    async def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """Get all members of a group from PostgreSQL"""
        return await postgres_client.get_group_members(group_id)

    async def get_user_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all groups a user is member of"""
        return await postgres_client.get_user_groups(user_id)

    async def get_recent_activity(self, group_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent activity from Redis stream"""
        return await redis_client.get_recent_activity(group_id, limit)


# Global instance
group_service = GroupService()
