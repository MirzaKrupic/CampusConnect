#!/usr/bin/env python3
"""
Seed script to populate demo data across all 4 databases
Demonstrates polyglot persistence initialization
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, "/app")

from backend.db.postgres import postgres_client
from backend.db.redis import redis_client
from backend.db.mongo import mongo_client
from backend.db.neo4j import neo4j_client

print("=" * 60)
print("CampusConnect Seed Script")
print("=" * 60)


async def seed_data():
    """Seed all databases with demo data"""

    # Connect to all databases
    print("\n1. Connecting to databases...")
    await postgres_client.connect()
    await redis_client.connect()
    await mongo_client.connect()
    await neo4j_client.connect()
    print("   ✓ All databases connected")

    # Create users
    print("\n2. Creating users in PostgreSQL...")
    users_data = [
        ("alice@university.edu", "Alice Johnson"),
        ("bob@university.edu", "Bob Smith"),
        ("charlie@university.edu", "Charlie Davis"),
        ("diana@university.edu", "Diana Martinez"),
        ("eve@university.edu", "Eve Wilson"),
        ("frank@university.edu", "Frank Brown"),
    ]

    users = []
    for email, full_name in users_data:
        user = await postgres_client.create_user(email, full_name)
        users.append(user)
        print(f"   ✓ Created user {user['id']}: {full_name}")

        # Create user node in Neo4j
        await neo4j_client.create_user_node(
            user["id"], user["email"], user["full_name"]
        )

        # Cache in Redis
        await redis_client.cache_user(user["id"], user)

    print(f"   ✓ Created {len(users)} users across PostgreSQL, Neo4j, and Redis")

    # Create friendships
    print("\n3. Creating friendships in Neo4j...")
    friendships = [
        (1, 2),  # Alice <-> Bob
        (1, 3),  # Alice <-> Charlie
        (2, 3),  # Bob <-> Charlie
        (2, 4),  # Bob <-> Diana
        (3, 4),  # Charlie <-> Diana
        (4, 5),  # Diana <-> Eve
        (5, 6),  # Eve <-> Frank
    ]

    for user1_id, user2_id in friendships:
        await neo4j_client.create_friendship(user1_id, user2_id)
        print(f"   ✓ Created friendship: User {user1_id} <-> User {user2_id}")

    # Create study groups
    print("\n4. Creating study groups in PostgreSQL...")
    groups_data = [
        ("Database Systems Study Group", "CS-401"),
        ("Web Development Workshop", "CS-350"),
        ("Machine Learning Enthusiasts", "CS-520"),
        ("Algorithms Practice", "CS-310"),
    ]

    groups = []
    for name, course_code in groups_data:
        group = await postgres_client.create_group(name, course_code)
        groups.append(group)
        print(f"   ✓ Created group {group['id']}: {name}")

        # Create group node in Neo4j
        await neo4j_client.create_group_node(group["id"], group["name"], group["course_code"])

        # Cache in Redis
        group_summary = {**group, "member_count": 0, "post_count": 0}
        await redis_client.cache_group(group["id"], group_summary)

    print(f"   ✓ Created {len(groups)} groups across PostgreSQL, Neo4j, and Redis")

    # Add group memberships
    print("\n5. Creating group memberships...")
    memberships = [
        (1, 1, "admin"),    # Alice -> Database Systems (admin)
        (2, 1, "member"),   # Bob -> Database Systems
        (3, 1, "member"),   # Charlie -> Database Systems
        (1, 2, "member"),   # Alice -> Web Development
        (2, 2, "admin"),    # Bob -> Web Development (admin)
        (4, 2, "member"),   # Diana -> Web Development
        (3, 3, "admin"),    # Charlie -> ML Enthusiasts (admin)
        (4, 3, "member"),   # Diana -> ML Enthusiasts
        (5, 3, "member"),   # Eve -> ML Enthusiasts
        (4, 4, "admin"),    # Diana -> Algorithms (admin)
        (5, 4, "member"),   # Eve -> Algorithms
        (6, 4, "member"),   # Frank -> Algorithms
    ]

    for user_id, group_id, role in memberships:
        await postgres_client.add_membership(user_id, group_id, role)
        await neo4j_client.create_membership(user_id, group_id, role)
        print(f"   ✓ User {user_id} joined Group {group_id} as {role}")

        # Award points
        await redis_client.increment_user_points(user_id, 5)

    # Create posts in MongoDB
    print("\n6. Creating posts in MongoDB...")
    posts_data = [
        {
            "author_id": 1,
            "group_id": 1,
            "post_type": "question",
            "title": "What are ACID properties?",
            "body": "Can someone explain ACID properties in simple terms?",
            "tags": ["databases", "acid", "transactions"],
        },
        {
            "author_id": 2,
            "group_id": 1,
            "post_type": "resource",
            "title": "Great PostgreSQL Tutorial",
            "body": "Found this amazing tutorial on PostgreSQL indexing: https://example.com/pg-tutorial",
            "tags": ["postgresql", "tutorial", "indexing"],
        },
        {
            "author_id": 3,
            "group_id": 1,
            "post_type": "note",
            "title": "Lecture Notes - Week 5",
            "body": "Here are my notes from this week's lecture on normalization...",
            "tags": ["lecture", "normalization", "notes"],
        },
        {
            "author_id": 2,
            "group_id": 2,
            "post_type": "question",
            "title": "React vs Vue?",
            "body": "Which framework should I learn for our project?",
            "tags": ["react", "vue", "javascript"],
        },
        {
            "author_id": 1,
            "group_id": 2,
            "post_type": "resource",
            "title": "FastAPI Documentation",
            "body": "Check out the official FastAPI docs - super helpful!",
            "tags": ["fastapi", "python", "backend"],
        },
        {
            "author_id": 3,
            "group_id": 3,
            "post_type": "resource",
            "title": "Introduction to Neural Networks",
            "body": "Great video series on neural networks: https://example.com/nn-series",
            "tags": ["ml", "neural-networks", "video"],
        },
        {
            "author_id": 4,
            "group_id": 3,
            "post_type": "question",
            "title": "TensorFlow vs PyTorch?",
            "body": "What are the pros and cons of each framework?",
            "tags": ["tensorflow", "pytorch", "frameworks"],
        },
        {
            "author_id": 5,
            "group_id": 4,
            "post_type": "note",
            "title": "Dynamic Programming Patterns",
            "body": "Summary of common DP patterns we covered in class...",
            "tags": ["algorithms", "dynamic-programming", "notes"],
        },
    ]

    import time
    for post_data in posts_data:
        post = await mongo_client.create_post(**post_data)
        print(f"   ✓ Created post: {post_data['title']}")

        # Add to hot posts
        timestamp_score = time.time()
        await redis_client.add_hot_post(post["_id"], timestamp_score)

        # Push activity
        from datetime import datetime
        activity = {
            "type": "post",
            "post_id": post["_id"],
            "author_id": post_data["author_id"],
            "group_id": post_data["group_id"],
            "title": post_data["title"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        await redis_client.push_activity(post_data["group_id"], activity)

        # Award points
        await redis_client.increment_user_points(post_data["author_id"], 10)

    print(f"   ✓ Created {len(posts_data)} posts in MongoDB")

    # Add some comments
    print("\n7. Creating comments in MongoDB...")
    # Get a post to comment on
    group1_posts = await mongo_client.get_group_posts(1, limit=1)
    if group1_posts:
        post_id = group1_posts[0]["_id"]
        comment = await mongo_client.create_comment(
            post_id, 2, "Great question! ACID stands for Atomicity, Consistency, Isolation, Durability..."
        )
        print(f"   ✓ Created comment on post {post_id}")
        await redis_client.increment_user_points(2, 2)

    # Disconnect
    print("\n8. Disconnecting from databases...")
    await postgres_client.disconnect()
    await redis_client.disconnect()
    await mongo_client.disconnect()
    await neo4j_client.disconnect()
    print("   ✓ All databases disconnected")

    print("\n" + "=" * 60)
    print("Seed completed successfully!")
    print("=" * 60)
    print("\nDemo data summary:")
    print(f"  • {len(users)} users created")
    print(f"  • {len(friendships)} friendships established")
    print(f"  • {len(groups)} study groups created")
    print(f"  • {len(memberships)} group memberships")
    print(f"  • {len(posts_data)} posts published")
    print(f"  • Comments and leaderboard initialized")
    print("\nYou can now access the API at http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(seed_data())
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
