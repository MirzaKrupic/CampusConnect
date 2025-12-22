"""
Unit tests for CampusConnect services
Demonstrates testing polyglot persistence patterns
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestUserService:
    """Test user service operations across PostgreSQL, Neo4j, and Redis"""

    @pytest.mark.asyncio
    async def test_create_user_writes_to_all_databases(self):
        """
        Test that creating a user writes to:
        1. PostgreSQL (source of truth)
        2. Neo4j (graph node)
        3. Redis (cache)
        """
        from backend.services.user_service import UserService

        service = UserService()

        # Mock database clients
        with patch("backend.services.user_service.postgres_client") as mock_pg, \
             patch("backend.services.user_service.neo4j_client") as mock_neo4j, \
             patch("backend.services.user_service.redis_client") as mock_redis:

            # Setup mocks
            mock_user = {
                "id": 1,
                "email": "test@example.com",
                "full_name": "Test User",
            }
            mock_pg.create_user = AsyncMock(return_value=mock_user)
            mock_neo4j.create_user_node = AsyncMock()
            mock_redis.cache_user = AsyncMock()

            # Execute
            result = await service.create_user("test@example.com", "Test User")

            # Assert all three databases were written to
            mock_pg.create_user.assert_called_once_with("test@example.com", "Test User")
            mock_neo4j.create_user_node.assert_called_once_with(
                user_id=1, email="test@example.com", full_name="Test User"
            )
            mock_redis.cache_user.assert_called_once_with(1, mock_user)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_user_uses_cache_aside_pattern(self):
        """
        Test cache-aside pattern:
        1. Try Redis first
        2. Fallback to PostgreSQL on miss
        3. Repopulate cache
        """
        from backend.services.user_service import UserService

        service = UserService()

        with patch("backend.services.user_service.postgres_client") as mock_pg, \
             patch("backend.services.user_service.redis_client") as mock_redis:

            # Simulate cache miss
            mock_redis.get_cached_user = AsyncMock(return_value=None)
            mock_user = {"id": 1, "email": "test@example.com", "full_name": "Test User"}
            mock_pg.get_user = AsyncMock(return_value=mock_user)
            mock_redis.cache_user = AsyncMock()

            # Execute
            result = await service.get_user(1)

            # Assert cache was checked first
            mock_redis.get_cached_user.assert_called_once_with(1)
            # Assert PostgreSQL was queried on cache miss
            mock_pg.get_user.assert_called_once_with(1)
            # Assert cache was repopulated
            mock_redis.cache_user.assert_called_once_with(1, mock_user)
            assert result == mock_user


class TestGroupService:
    """Test group service multi-database coordination"""

    @pytest.mark.asyncio
    async def test_join_group_coordinates_multiple_writes(self):
        """
        Test that joining a group writes to:
        1. PostgreSQL (membership record)
        2. Neo4j (MEMBER_OF relationship)
        3. Redis (activity stream, cache invalidation, points)
        """
        from backend.services.group_service import GroupService

        service = GroupService()

        with patch("backend.services.group_service.postgres_client") as mock_pg, \
             patch("backend.services.group_service.neo4j_client") as mock_neo4j, \
             patch("backend.services.group_service.redis_client") as mock_redis:

            # Setup mocks
            mock_membership = {"user_id": 1, "group_id": 1, "role": "member"}
            mock_pg.add_membership = AsyncMock(return_value=mock_membership)
            mock_neo4j.create_membership = AsyncMock()
            mock_redis.push_activity = AsyncMock()
            mock_redis.invalidate_group_cache = AsyncMock()
            mock_redis.increment_user_points = AsyncMock()

            # Execute
            result = await service.join_group(1, 1, "member")

            # Assert all operations occurred
            mock_pg.add_membership.assert_called_once()
            mock_neo4j.create_membership.assert_called_once()
            mock_redis.push_activity.assert_called_once()
            mock_redis.invalidate_group_cache.assert_called_once_with(1)
            mock_redis.increment_user_points.assert_called_once_with(1, points=5)
            assert result == mock_membership


class TestPostService:
    """Test post service MongoDB + Redis operations"""

    @pytest.mark.asyncio
    async def test_create_post_writes_to_mongo_and_redis(self):
        """
        Test that creating a post:
        1. Stores document in MongoDB
        2. Adds to Redis hot posts
        3. Pushes to Redis activity stream
        4. Awards points
        """
        from backend.services.post_service import PostService

        service = PostService()

        with patch("backend.services.post_service.mongo_client") as mock_mongo, \
             patch("backend.services.post_service.postgres_client") as mock_pg, \
             patch("backend.services.post_service.redis_client") as mock_redis:

            # Setup mocks
            mock_pg.is_member = AsyncMock(return_value=True)
            mock_post = {"_id": "post123", "title": "Test Post"}
            mock_mongo.create_post = AsyncMock(return_value=mock_post)
            mock_redis.add_hot_post = AsyncMock()
            mock_redis.push_activity = AsyncMock()
            mock_redis.increment_user_points = AsyncMock()
            mock_redis.invalidate_group_cache = AsyncMock()

            # Execute
            result = await service.create_post(
                author_id=1,
                group_id=1,
                post_type="note",
                title="Test Post",
                body="Test body",
            )

            # Assert MongoDB write
            mock_mongo.create_post.assert_called_once()
            # Assert Redis operations
            mock_redis.add_hot_post.assert_called_once()
            mock_redis.push_activity.assert_called_once()
            mock_redis.increment_user_points.assert_called_once_with(1, points=10)
            assert result == mock_post

    @pytest.mark.asyncio
    async def test_get_group_feed_enriches_from_multiple_sources(self):
        """
        Test that feed retrieval:
        1. Gets posts from MongoDB
        2. Enriches with author data from PostgreSQL
        3. Enriches with group data from PostgreSQL
        """
        from backend.services.post_service import PostService

        service = PostService()

        with patch("backend.services.post_service.mongo_client") as mock_mongo, \
             patch("backend.services.post_service.postgres_client") as mock_pg:

            # Setup mocks
            mock_posts = [
                {"_id": "1", "author_id": 1, "group_id": 1, "title": "Post 1"},
                {"_id": "2", "author_id": 2, "group_id": 1, "title": "Post 2"},
            ]
            mock_mongo.get_group_posts = AsyncMock(return_value=mock_posts)

            mock_author1 = {"full_name": "Author 1", "email": "author1@test.com"}
            mock_author2 = {"full_name": "Author 2", "email": "author2@test.com"}
            mock_group = {"name": "Test Group"}

            mock_pg.get_user = AsyncMock(side_effect=[mock_author1, mock_author2])
            mock_pg.get_group = AsyncMock(return_value=mock_group)

            # Execute
            result = await service.get_group_feed(1, limit=20)

            # Assert enrichment
            assert len(result) == 2
            assert result[0]["author_name"] == "Author 1"
            assert result[1]["author_name"] == "Author 2"
            assert result[0]["group_name"] == "Test Group"


class TestRecommendationService:
    """Test Neo4j graph-based recommendations"""

    @pytest.mark.asyncio
    async def test_recommend_friends_uses_graph_traversal(self):
        """
        Test that friend recommendations use Neo4j graph queries
        for friend-of-friend pattern
        """
        from backend.services.recommendation_service import RecommendationService

        service = RecommendationService()

        with patch("backend.services.recommendation_service.neo4j_client") as mock_neo4j:

            mock_recommendations = [
                {
                    "user_id": 3,
                    "full_name": "Potential Friend",
                    "email": "friend@test.com",
                    "mutual_friends": 2,
                    "reason": "2 mutual friends",
                }
            ]
            mock_neo4j.recommend_friends = AsyncMock(return_value=mock_recommendations)

            # Execute
            result = await service.recommend_friends(1, limit=10)

            # Assert Neo4j was called
            mock_neo4j.recommend_friends.assert_called_once_with(1, 10)
            assert result == mock_recommendations
            assert result[0]["mutual_friends"] == 2


# Run tests with: pytest backend/tests/test_services.py -v
