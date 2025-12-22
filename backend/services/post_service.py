"""
Post Service - Handles content operations via MongoDB with Redis caching
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import time

from backend.db.mongo import mongo_client
from backend.db.postgres import postgres_client
from backend.db.redis import redis_client

logger = logging.getLogger(__name__)


class PostService:
    """
    Orchestrates post/content operations across:
    - MongoDB: flexible document storage for posts/comments
    - PostgreSQL: user/group metadata for enrichment
    - Redis: hot posts cache and activity streams
    """

    async def create_post(
        self,
        author_id: int,
        group_id: int,
        post_type: str,
        title: str,
        body: str,
        tags: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Create post in MongoDB, update Redis hot posts and activity
        """
        # Verify user is member of group
        is_member = await postgres_client.is_member(author_id, group_id)
        if not is_member:
            raise ValueError("User is not a member of this group")

        # 1. Create post in MongoDB
        post = await mongo_client.create_post(
            author_id=author_id,
            group_id=group_id,
            post_type=post_type,
            title=title,
            body=body,
            tags=tags or [],
        )
        logger.info(f"Created post {post['_id']} in MongoDB")

        # 2. Add to hot posts in Redis (score = timestamp for recency)
        timestamp_score = time.time()
        await redis_client.add_hot_post(post["_id"], timestamp_score)
        logger.info(f"Added post {post['_id']} to hot posts")

        # 3. Push to group activity stream
        activity = {
            "type": "post",
            "post_id": post["_id"],
            "author_id": author_id,
            "group_id": group_id,
            "title": title,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await redis_client.push_activity(group_id, activity)

        # 4. Award points for creating content
        await redis_client.increment_user_points(author_id, points=10)

        # 5. Invalidate group cache (post_count changed)
        await redis_client.invalidate_group_cache(group_id)

        return post

    async def get_group_feed(
        self, group_id: int, limit: int = 20, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get feed for a group with enriched data:
        - Posts from MongoDB
        - Author info from PostgreSQL (with Redis cache)
        - Group info from PostgreSQL (with Redis cache)

        Demonstrates cross-database enrichment pattern
        """
        # 1. Get posts from MongoDB
        posts = await mongo_client.get_group_posts(group_id, limit, skip)
        logger.info(f"Retrieved {len(posts)} posts from MongoDB for group {group_id}")

        # 2. Enrich with author and group data
        enriched_posts = []
        for post in posts:
            # Get author info (cache-aside via Redis)
            author = await postgres_client.get_user(post["author_id"])

            # Get group info (cache-aside via Redis)
            group = await postgres_client.get_group(post["group_id"])

            enriched_post = {
                **post,
                "id": post["_id"],  # Rename _id to id for response model
                "author_name": author["full_name"] if author else "Unknown",
                "author_email": author["email"] if author else "unknown@example.com",
                "group_name": group["name"] if group else "Unknown Group",
            }
            enriched_posts.append(enriched_post)

        return enriched_posts

    async def get_hot_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get hot posts from Redis, then enrich from MongoDB and PostgreSQL
        Demonstrates Redis as fast access layer
        """
        # 1. Get hot post IDs from Redis (fast)
        hot_post_ids = await redis_client.get_hot_posts(limit)
        logger.info(f"Retrieved {len(hot_post_ids)} hot post IDs from Redis")

        # 2. Fetch full post data from MongoDB
        enriched_posts = []
        for post_id in hot_post_ids:
            post = await mongo_client.get_post(post_id)
            if post:
                # Enrich with author data
                author = await postgres_client.get_user(post["author_id"])
                post["author_name"] = author["full_name"] if author else "Unknown"
                enriched_posts.append(post)

        return enriched_posts

    async def create_comment(
        self, post_id: str, author_id: int, body: str
    ) -> Dict[str, Any]:
        """Create comment in MongoDB and award points"""
        comment = await mongo_client.create_comment(post_id, author_id, body)

        # Award points for engagement
        await redis_client.increment_user_points(author_id, points=2)

        return comment

    async def get_post_comments(self, post_id: str) -> List[Dict[str, Any]]:
        """Get comments with author enrichment"""
        comments = await mongo_client.get_post_comments(post_id)

        # Enrich with author names
        enriched_comments = []
        for comment in comments:
            author = await postgres_client.get_user(comment["author_id"])
            comment["author_name"] = author["full_name"] if author else "Unknown"
            enriched_comments.append(comment)

        return enriched_comments


# Global instance
post_service = PostService()
