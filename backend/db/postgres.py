"""
PostgreSQL Client - System of Record
Handles transactional data: users, groups, memberships
"""
import asyncpg
from typing import Optional, List, Dict, Any
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class PostgresClient:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                min_size=2,
                max_size=10,
            )
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    # User operations
    async def create_user(self, email: str, full_name: str) -> Dict[str, Any]:
        """Create a new user"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, full_name)
                VALUES ($1, $2)
                RETURNING id, email, full_name, created_at
                """,
                email,
                full_name,
            )
            return dict(row)

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, full_name, created_at FROM users WHERE id = $1",
                user_id,
            )
            return dict(row) if row else None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, full_name, created_at FROM users WHERE email = $1",
                email,
            )
            return dict(row) if row else None

    # Group operations
    async def create_group(self, name: str, course_code: str) -> Dict[str, Any]:
        """Create a new group"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO groups (name, course_code)
                VALUES ($1, $2)
                RETURNING id, name, course_code, created_at
                """,
                name,
                course_code,
            )
            return dict(row)

    async def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get group by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, course_code, created_at FROM groups WHERE id = $1",
                group_id,
            )
            return dict(row) if row else None

    async def get_groups(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all groups"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, course_code, created_at FROM groups ORDER BY created_at DESC LIMIT $1",
                limit,
            )
            return [dict(row) for row in rows]

    # Membership operations
    async def add_membership(
        self, user_id: int, group_id: int, role: str = "member"
    ) -> Dict[str, Any]:
        """Add user to group"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO group_memberships (user_id, group_id, role)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, group_id) DO UPDATE SET role = $3
                RETURNING user_id, group_id, role, joined_at
                """,
                user_id,
                group_id,
                role,
            )
            return dict(row)

    async def get_user_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all groups for a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT g.id, g.name, g.course_code, g.created_at, gm.role, gm.joined_at
                FROM groups g
                JOIN group_memberships gm ON g.id = gm.group_id
                WHERE gm.user_id = $1
                ORDER BY gm.joined_at DESC
                """,
                user_id,
            )
            return [dict(row) for row in rows]

    async def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """Get all members of a group"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT u.id, u.email, u.full_name, gm.role, gm.joined_at
                FROM users u
                JOIN group_memberships gm ON u.id = gm.user_id
                WHERE gm.group_id = $1
                ORDER BY gm.joined_at ASC
                """,
                group_id,
            )
            return [dict(row) for row in rows]

    async def is_member(self, user_id: int, group_id: int) -> bool:
        """Check if user is a member of group"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM group_memberships WHERE user_id = $1 AND group_id = $2",
                user_id,
                group_id,
            )
            return row is not None


# Global instance
postgres_client = PostgresClient()
