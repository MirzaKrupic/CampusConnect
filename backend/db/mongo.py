"""
MongoDB Client - Flexible Content Storage
Handles posts, comments, and flexible document structures
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class MongoClient:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

    async def connect(self):
        """Initialize MongoDB connection"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_uri)
            self.db = self.client[settings.mongodb_db]
            # Test connection
            await self.client.admin.command("ping")
            logger.info("MongoDB connection established")

            # Create indexes
            await self._create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def _create_indexes(self):
        """Create indexes for better query performance"""
        # Posts indexes
        await self.db.posts.create_index("group_id")
        await self.db.posts.create_index("author_id")
        await self.db.posts.create_index([("created_at", -1)])
        await self.db.posts.create_index("tags")

        # Comments indexes
        await self.db.comments.create_index("post_id")
        await self.db.comments.create_index("author_id")
        await self.db.comments.create_index([("created_at", -1)])

        logger.info("MongoDB indexes created")

    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    # Post operations
    async def create_post(
        self,
        author_id: int,
        group_id: int,
        post_type: str,
        title: str,
        body: str,
        tags: List[str] = None,
        attachments: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new post"""
        post = {
            "author_id": author_id,
            "group_id": group_id,
            "type": post_type,  # "resource", "question", "note"
            "title": title,
            "body": body,
            "tags": tags or [],
            "attachments": attachments or [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await self.db.posts.insert_one(post)
        post["_id"] = str(result.inserted_id)
        logger.info(f"Created post {post['_id']} in group {group_id}")
        return post

    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post by ID"""
        from bson import ObjectId

        try:
            post = await self.db.posts.find_one({"_id": ObjectId(post_id)})
            if post:
                post["_id"] = str(post["_id"])
            return post
        except Exception as e:
            logger.error(f"Error fetching post {post_id}: {e}")
            return None

    async def get_group_posts(
        self, group_id: int, limit: int = 20, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get posts for a group (paginated, sorted by newest first)"""
        cursor = (
            self.db.posts.find({"group_id": group_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        posts = []
        async for post in cursor:
            post["_id"] = str(post["_id"])
            posts.append(post)

        logger.debug(f"Retrieved {len(posts)} posts for group {group_id}")
        return posts

    async def get_user_posts(
        self, author_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get posts by a user"""
        cursor = (
            self.db.posts.find({"author_id": author_id})
            .sort("created_at", -1)
            .limit(limit)
        )

        posts = []
        async for post in cursor:
            post["_id"] = str(post["_id"])
            posts.append(post)

        return posts

    async def search_posts_by_tags(
        self, tags: List[str], limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search posts by tags"""
        cursor = (
            self.db.posts.find({"tags": {"$in": tags}})
            .sort("created_at", -1)
            .limit(limit)
        )

        posts = []
        async for post in cursor:
            post["_id"] = str(post["_id"])
            posts.append(post)

        return posts

    # Comment operations
    async def create_comment(
        self, post_id: str, author_id: int, body: str
    ) -> Dict[str, Any]:
        """Create a comment on a post"""
        from bson import ObjectId

        comment = {
            "post_id": ObjectId(post_id),
            "author_id": author_id,
            "body": body,
            "created_at": datetime.utcnow(),
        }

        result = await self.db.comments.insert_one(comment)
        comment["_id"] = str(result.inserted_id)
        comment["post_id"] = post_id
        logger.info(f"Created comment {comment['_id']} on post {post_id}")
        return comment

    async def get_post_comments(
        self, post_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get comments for a post"""
        from bson import ObjectId

        cursor = (
            self.db.comments.find({"post_id": ObjectId(post_id)})
            .sort("created_at", 1)
            .limit(limit)
        )

        comments = []
        async for comment in cursor:
            comment["_id"] = str(comment["_id"])
            comment["post_id"] = str(comment["post_id"])
            comments.append(comment)

        return comments

    async def get_post_count(self, group_id: int) -> int:
        """Get total number of posts in a group"""
        count = await self.db.posts.count_documents({"group_id": group_id})
        return count


# Global instance
mongo_client = MongoClient()
