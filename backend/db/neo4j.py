"""
Neo4j Client - Graph Relationships
Handles social graph: friendships, group memberships, recommendations
"""
from neo4j import AsyncGraphDatabase
from typing import Optional, List, Dict, Any
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self):
        self.driver = None

    async def connect(self):
        """Initialize Neo4j connection"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            # Test connection
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            logger.info("Neo4j connection established")

            # Create constraints and indexes
            await self._create_constraints()
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def _create_constraints(self):
        """Create uniqueness constraints and indexes"""
        async with self.driver.session() as session:
            # User node constraint
            await session.run(
                "CREATE CONSTRAINT user_id_unique IF NOT EXISTS "
                "FOR (u:User) REQUIRE u.id IS UNIQUE"
            )
            # Group node constraint
            await session.run(
                "CREATE CONSTRAINT group_id_unique IF NOT EXISTS "
                "FOR (g:Group) REQUIRE g.id IS UNIQUE"
            )
            logger.info("Neo4j constraints created")

    async def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    # Node operations
    async def create_user_node(self, user_id: int, email: str, full_name: str):
        """Create User node in graph"""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (u:User {id: $user_id})
                SET u.email = $email, u.full_name = $full_name
                RETURN u
                """,
                user_id=user_id,
                email=email,
                full_name=full_name,
            )
            logger.info(f"Created User node {user_id} in Neo4j")

    async def create_group_node(self, group_id: int, name: str, course_code: str):
        """Create Group node in graph"""
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (g:Group {id: $group_id})
                SET g.name = $name, g.course_code = $course_code
                RETURN g
                """,
                group_id=group_id,
                name=name,
                course_code=course_code,
            )
            logger.info(f"Created Group node {group_id} in Neo4j")

    # Relationship operations
    async def create_friendship(self, user1_id: int, user2_id: int):
        """Create bidirectional FRIEND relationship"""
        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (u1:User {id: $user1_id})
                MATCH (u2:User {id: $user2_id})
                MERGE (u1)-[:FRIEND]->(u2)
                MERGE (u2)-[:FRIEND]->(u1)
                """,
                user1_id=user1_id,
                user2_id=user2_id,
            )
            logger.info(f"Created friendship between {user1_id} and {user2_id}")

    async def create_membership(self, user_id: int, group_id: int, role: str = "member"):
        """Create MEMBER_OF relationship"""
        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (u:User {id: $user_id})
                MATCH (g:Group {id: $group_id})
                MERGE (u)-[r:MEMBER_OF]->(g)
                SET r.role = $role
                """,
                user_id=user_id,
                group_id=group_id,
                role=role,
            )
            logger.info(f"Created membership: User {user_id} -> Group {group_id}")

    async def are_friends(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users are friends"""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (u1:User {id: $user1_id})-[:FRIEND]->(u2:User {id: $user2_id})
                RETURN COUNT(*) > 0 as are_friends
                """,
                user1_id=user1_id,
                user2_id=user2_id,
            )
            record = await result.single()
            return record["are_friends"] if record else False

    # Recommendation queries
    async def recommend_friends(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend friends-of-friends who are not already friends
        Returns mutual friend count for ranking
        """
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (me:User {id: $user_id})-[:FRIEND]->(friend)-[:FRIEND]->(fof:User)
                WHERE me <> fof
                  AND NOT (me)-[:FRIEND]->(fof)
                WITH fof, COUNT(DISTINCT friend) as mutual_friends
                ORDER BY mutual_friends DESC
                LIMIT $limit
                RETURN fof.id as user_id, fof.full_name as full_name,
                       fof.email as email, mutual_friends
                """,
                user_id=user_id,
                limit=limit,
            )

            recommendations = []
            async for record in result:
                recommendations.append(
                    {
                        "user_id": record["user_id"],
                        "full_name": record["full_name"],
                        "email": record["email"],
                        "mutual_friends": record["mutual_friends"],
                        "reason": f"{record['mutual_friends']} mutual friends",
                    }
                )

            logger.debug(f"Found {len(recommendations)} friend recommendations for user {user_id}")
            return recommendations

    async def recommend_groups(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend groups based on:
        1. Groups that user's friends are in
        2. Groups with similar course codes to user's current groups
        """
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (me:User {id: $user_id})-[:FRIEND]->(friend)-[:MEMBER_OF]->(g:Group)
                WHERE NOT (me)-[:MEMBER_OF]->(g)
                WITH g, COUNT(DISTINCT friend) as friend_count
                ORDER BY friend_count DESC
                LIMIT $limit
                RETURN g.id as group_id, g.name as name,
                       g.course_code as course_code, friend_count
                """,
                user_id=user_id,
                limit=limit,
            )

            recommendations = []
            async for record in result:
                recommendations.append(
                    {
                        "group_id": record["group_id"],
                        "name": record["name"],
                        "course_code": record["course_code"],
                        "friend_count": record["friend_count"],
                        "reason": f"{record['friend_count']} friends in this group",
                    }
                )

            logger.debug(f"Found {len(recommendations)} group recommendations for user {user_id}")
            return recommendations

    async def get_common_groups(self, user1_id: int, user2_id: int) -> List[Dict[str, Any]]:
        """Find groups that both users are members of"""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (u1:User {id: $user1_id})-[:MEMBER_OF]->(g:Group)<-[:MEMBER_OF]-(u2:User {id: $user2_id})
                RETURN g.id as group_id, g.name as name, g.course_code as course_code
                """,
                user1_id=user1_id,
                user2_id=user2_id,
            )

            groups = []
            async for record in result:
                groups.append(
                    {
                        "group_id": record["group_id"],
                        "name": record["name"],
                        "course_code": record["course_code"],
                    }
                )
            return groups

    async def get_user_degree(self, user_id: int) -> int:
        """Get number of friends (node degree)"""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (u:User {id: $user_id})-[:FRIEND]->()
                RETURN COUNT(*) as degree
                """,
                user_id=user_id,
            )
            record = await result.single()
            return record["degree"] if record else 0


# Global instance
neo4j_client = Neo4jClient()
