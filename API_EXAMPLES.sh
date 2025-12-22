#!/bin/bash

# CampusConnect API Examples
# Comprehensive curl examples for all endpoints
# Usage: bash API_EXAMPLES.sh

set -e

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "CampusConnect API Examples"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health Check
echo -e "${BLUE}0. Health Check${NC}"
curl -s $BASE_URL/health | python3 -m json.tool
echo ""
echo ""

# 1. Create User
echo -e "${BLUE}1. Create User (PostgreSQL + Neo4j + Redis)${NC}"
echo "Creating new user..."
curl -X POST $BASE_URL/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@university.edu",
    "full_name": "New Student"
  }' | python3 -m json.tool
echo ""
echo ""

# 2. Get User Profile
echo -e "${BLUE}2. Get User Profile (Redis cache → PostgreSQL fallback)${NC}"
echo "Fetching user 1..."
curl -s $BASE_URL/users/1 | python3 -m json.tool
echo ""
echo ""

# 3. Add Friend
echo -e "${BLUE}3. Add Friend (Neo4j relationship)${NC}"
echo "Making user 1 and user 5 friends..."
curl -X POST $BASE_URL/users/1/friends/5 | python3 -m json.tool
echo ""
echo ""

# 4. Create Group
echo -e "${BLUE}4. Create Study Group (PostgreSQL + Neo4j + Redis)${NC}"
echo "Creating new study group..."
curl -X POST $BASE_URL/groups \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cloud Computing Study Group",
    "course_code": "CS-480"
  }' | python3 -m json.tool
echo ""
echo ""

# 5. Join Group
echo -e "${BLUE}5. Join Group (Multi-DB write: PostgreSQL + Neo4j + Redis)${NC}"
echo "User 1 joining group 1..."
curl -X POST $BASE_URL/groups/1/join \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "role": "member"
  }' | python3 -m json.tool
echo ""
echo ""

# Get Group Members
echo -e "${BLUE}5a. Get Group Members (PostgreSQL)${NC}"
echo "Fetching members of group 1..."
curl -s $BASE_URL/groups/1/members | python3 -m json.tool
echo ""
echo ""

# Get Group Activity
echo -e "${BLUE}5b. Get Recent Activity (Redis stream)${NC}"
echo "Fetching recent activity for group 1..."
curl -s "$BASE_URL/groups/1/activity?limit=5" | python3 -m json.tool
echo ""
echo ""

# 6. Create Post
echo -e "${BLUE}6. Create Post (MongoDB + Redis hot posts + activity)${NC}"
echo "Creating post in group 1..."
curl -X POST $BASE_URL/groups/1/posts \
  -H "Content-Type: application/json" \
  -d '{
    "author_id": 1,
    "type": "resource",
    "title": "Great Article on Polyglot Persistence",
    "body": "Check out this article explaining why companies use multiple databases: https://example.com/article",
    "tags": ["databases", "architecture", "polyglot"]
  }' | python3 -m json.tool
echo ""
echo ""

# 7. Get Group Feed
echo -e "${BLUE}7. Get Group Feed (MongoDB + PostgreSQL enrichment)${NC}"
echo "Fetching feed for group 1..."
curl -s "$BASE_URL/groups/1/posts/feed?limit=5" | python3 -m json.tool
echo ""
echo ""

# 8. Friend Recommendations
echo -e "${BLUE}8. Friend Recommendations (Neo4j graph traversal)${NC}"
echo "Getting friend recommendations for user 1..."
echo -e "${GREEN}Neo4j Query: Friend-of-friend pattern matching${NC}"
curl -s "$BASE_URL/recommendations/users/1/friends?limit=5" | python3 -m json.tool
echo ""
echo ""

# 9. Group Recommendations
echo -e "${BLUE}9. Group Recommendations (Neo4j friend network)${NC}"
echo "Getting group recommendations for user 1..."
echo -e "${GREEN}Neo4j Query: Groups where friends are members${NC}"
curl -s "$BASE_URL/recommendations/users/1/groups?limit=5" | python3 -m json.tool
echo ""
echo ""

# 10. Leaderboard
echo -e "${BLUE}10. Leaderboard (Redis sorted set)${NC}"
echo "Getting top 10 contributors..."
echo -e "${GREEN}Redis: ZREVRANGE O(log N) operation${NC}"
curl -s "$BASE_URL/recommendations/leaderboard?limit=10" | python3 -m json.tool
echo ""
echo ""

# Additional examples
echo "=========================================="
echo "Additional API Calls"
echo "=========================================="
echo ""

# Get specific group
echo -e "${BLUE}Get Group Details${NC}"
curl -s $BASE_URL/groups/2 | python3 -m json.tool
echo ""
echo ""

# Create another post
echo -e "${BLUE}Create Question Post${NC}"
curl -X POST $BASE_URL/groups/1/posts \
  -H "Content-Type: application/json" \
  -d '{
    "author_id": 2,
    "type": "question",
    "title": "How to optimize Neo4j queries?",
    "body": "Any tips for making Cypher queries faster?",
    "tags": ["neo4j", "performance", "question"]
  }' | python3 -m json.tool
echo ""
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}All Examples Completed!${NC}"
echo "=========================================="
echo ""
echo "Database operations demonstrated:"
echo "  ✓ PostgreSQL: Users, groups, memberships"
echo "  ✓ Redis: Caching, leaderboards, activity streams"
echo "  ✓ MongoDB: Flexible post documents"
echo "  ✓ Neo4j: Graph relationships and recommendations"
echo ""
echo "Next steps:"
echo "  - View API docs: http://localhost:8000/docs"
echo "  - Explore Neo4j: http://localhost:7474"
echo "  - Check leaderboard: curl $BASE_URL/recommendations/leaderboard"
echo "  - Read README.md for architecture details"
echo ""
