"""
Redis Client - Fast Layer
Handles caching, leaderboards, rate limiting, and recent activity streams
"""
import redis.asyncio as redis
import json
from typing import Optional, List, Dict, Any
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
            )
            await self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    # Cache operations
    async def cache_user(self, user_id: int, user_data: Dict[str, Any], ttl: int = 3600):
        """Cache user profile (1 hour TTL)"""
        key = f"user:{user_id}"
        await self.client.setex(key, ttl, json.dumps(user_data, default=str))
        logger.debug(f"Cached user {user_id}")

    async def get_cached_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        key = f"user:{user_id}"
        data = await self.client.get(key)
        if data:
            logger.debug(f"Cache hit for user {user_id}")
            return json.loads(data)
        logger.debug(f"Cache miss for user {user_id}")
        return None

    async def cache_group(self, group_id: int, group_data: Dict[str, Any], ttl: int = 3600):
        """Cache group summary (1 hour TTL)"""
        key = f"group:{group_id}"
        await self.client.setex(key, ttl, json.dumps(group_data, default=str))
        logger.debug(f"Cached group {group_id}")

    async def get_cached_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get cached group summary"""
        key = f"group:{group_id}"
        data = await self.client.get(key)
        if data:
            logger.debug(f"Cache hit for group {group_id}")
            return json.loads(data)
        logger.debug(f"Cache miss for group {group_id}")
        return None

    async def invalidate_user_cache(self, user_id: int):
        """Invalidate user cache"""
        key = f"user:{user_id}"
        await self.client.delete(key)
        logger.debug(f"Invalidated cache for user {user_id}")

    async def invalidate_group_cache(self, group_id: int):
        """Invalidate group cache"""
        key = f"group:{group_id}"
        await self.client.delete(key)
        logger.debug(f"Invalidated cache for group {group_id}")

    # Leaderboard operations (sorted sets)
    async def increment_user_points(self, user_id: int, points: int = 1):
        """Increment user participation points"""
        await self.client.zincrby("leaderboard:points", points, str(user_id))
        logger.debug(f"Incremented points for user {user_id} by {points}")

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by points (descending)"""
        results = await self.client.zrevrange(
            "leaderboard:points", 0, limit - 1, withscores=True
        )
        return [
            {"user_id": int(user_id), "points": int(score)}
            for user_id, score in results
        ]

    async def get_user_rank(self, user_id: int) -> Optional[int]:
        """Get user rank (0-indexed, lower is better)"""
        rank = await self.client.zrevrank("leaderboard:points", str(user_id))
        return rank

    # Recent activity streams (lists)
    async def push_activity(self, group_id: int, activity: Dict[str, Any], max_size: int = 100):
        """Push activity to group's recent stream"""
        key = f"recent:group:{group_id}"
        await self.client.lpush(key, json.dumps(activity, default=str))
        await self.client.ltrim(key, 0, max_size - 1)  # Keep only last N items
        logger.debug(f"Pushed activity to group {group_id}")

    async def get_recent_activity(self, group_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent activity for a group"""
        key = f"recent:group:{group_id}"
        activities = await self.client.lrange(key, 0, limit - 1)
        return [json.loads(activity) for activity in activities]

    # Hot posts (sorted sets with timestamp scores)
    async def add_hot_post(self, post_id: str, score: float):
        """Add post to hot posts sorted set"""
        await self.client.zadd("hot:posts", {post_id: score})
        logger.debug(f"Added post {post_id} to hot posts with score {score}")

    async def get_hot_posts(self, limit: int = 10) -> List[str]:
        """Get hot posts (most recent/highest scored)"""
        post_ids = await self.client.zrevrange("hot:posts", 0, limit - 1)
        return list(post_ids)

    # Rate limiting (simple counter with TTL)
    async def check_rate_limit(
        self, user_id: int, window_seconds: int = 60, max_requests: int = 100
    ) -> bool:
        """
        Check if user is within rate limit
        Returns True if allowed, False if rate limited
        """
        key = f"ratelimit:user:{user_id}"
        current = await self.client.get(key)

        if current is None:
            # First request in window
            await self.client.setex(key, window_seconds, 1)
            return True

        if int(current) >= max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False

        await self.client.incr(key)
        return True


# Global instance
redis_client = RedisClient()
