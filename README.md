# CampusConnect - Polyglot Persistence Demo

A real-world demonstration of **polyglot persistence** using PostgreSQL, Redis, MongoDB, and Neo4j to handle different data access patterns in a university campus social platform.

## Why Multiple Databases?

**Polyglot persistence** means using different databases for different data needs. Each database type excels at specific patterns:

| Database | Use Case | Why This DB? | What Would Go Wrong With Just SQL? |
|----------|----------|--------------|-------------------------------------|
| **PostgreSQL** | Users, groups, memberships | ACID transactions, referential integrity, authoritative records | ✅ Works fine - relational data is SQL's strength |
| **Redis** | Caching, leaderboards, rate limiting, activity streams | In-memory speed, atomic operations, O(1) lookups, sorted sets | ⚠️ Slow: Real-time leaderboards need ORDER BY on every query. Cache-aside requires app-level code. No native sorted sets. |
| **MongoDB** | Posts, comments, attachments | Flexible schema, nested documents, fast writes, horizontal scaling | ⚠️ Rigid: Post schema evolution requires migrations. JSON columns are harder to query. Denormalization becomes complex. |
| **Neo4j** | Friend relationships, recommendations | Graph traversals, pattern matching, social queries | ❌ Terrible: Friend-of-friend queries need multiple self-joins. Recommendation queries become O(N²) or worse. |

### Real-World Query Complexity Comparison

**Friend-of-Friend Recommendations:**

<details>
<summary>PostgreSQL (Complex, Slow)</summary>

```sql
-- Requires multiple self-joins, complex subqueries
SELECT u3.id, u3.full_name, COUNT(DISTINCT u2.id) as mutual_friends
FROM users u1
JOIN friendships f1 ON u1.id = f1.user1_id
JOIN users u2 ON f1.user2_id = u2.id
JOIN friendships f2 ON u2.id = f2.user1_id
JOIN users u3 ON f2.user2_id = u3.id
LEFT JOIN friendships f3 ON (u1.id = f3.user1_id AND u3.id = f3.user2_id)
WHERE u1.id = $1
  AND u3.id != $1
  AND f3.id IS NULL
GROUP BY u3.id, u3.full_name
ORDER BY mutual_friends DESC
LIMIT 10;
-- Complexity: O(N²) - scans entire friendship table multiple times
```
</details>

<details>
<summary>Neo4j (Simple, Fast)</summary>

```cypher
// Natural graph pattern matching
MATCH (me:User {id: $userId})-[:FRIEND]->(friend)-[:FRIEND]->(fof:User)
WHERE me <> fof AND NOT (me)-[:FRIEND]->(fof)
WITH fof, COUNT(DISTINCT friend) as mutual_friends
ORDER BY mutual_friends DESC
LIMIT 10
RETURN fof, mutual_friends
// Complexity: O(k*d²) where k=friends, d=average degree - much faster
```
</details>

**Leaderboard Queries:**

<details>
<summary>PostgreSQL (Table Scan)</summary>

```sql
-- Full table scan with ORDER BY
SELECT user_id, points
FROM user_points
ORDER BY points DESC
LIMIT 10;
-- Every update requires recomputing ORDER BY
-- Complexity: O(N log N) per query
```
</details>

<details>
<summary>Redis (O(log N))</summary>

```redis
# Sorted set operations
ZINCRBY leaderboard:points 10 user:123  # O(log N)
ZREVRANGE leaderboard:points 0 9 WITHSCORES  # O(log N + M)
# Native sorted set structure, no recomputation
```
</details>

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│                    (Service Layer)                          │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │ │   MongoDB    │ │    Neo4j     │
│              │ │              │ │              │ │              │
│ • Users      │ │ • Cache      │ │ • Posts      │ │ • User nodes │
│ • Groups     │ │ • Leaderboard│ │ • Comments   │ │ • Group nodes│
│ • Membership │ │ • Activity   │ │ • Attachments│ │ • FRIEND     │
│ • ACID Txn   │ │ • Rate Limit │ │ • Flexible   │ │ • MEMBER_OF  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### Data Flow Examples

**Creating a User:**
1. Write to PostgreSQL (source of truth)
2. Create node in Neo4j (for graph queries)
3. Cache profile in Redis (for fast reads)

**Joining a Group:**
1. Insert membership in PostgreSQL
2. Create MEMBER_OF relationship in Neo4j
3. Push activity to Redis stream
4. Invalidate group cache in Redis
5. Increment participation points in Redis

**Getting Group Feed:**
1. Query posts from MongoDB (flexible documents)
2. Enrich with author data from PostgreSQL (via Redis cache)
3. Enrich with group data from PostgreSQL (via Redis cache)
4. Return combined result

---

## Project Structure

```
campusconnect/
├── docker-compose.yml          # Orchestrates all 4 databases + backend
├── Dockerfile                  # Backend container
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
│
├── backend/
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Configuration management
│   │
│   ├── db/                    # Database clients (clean separation)
│   │   ├── postgres.py        # PostgreSQL connection + queries
│   │   ├── redis.py           # Redis operations
│   │   ├── mongo.py           # MongoDB operations
│   │   └── neo4j.py           # Neo4j Cypher queries
│   │
│   ├── models/                # Pydantic models for validation
│   │   ├── user.py
│   │   ├── group.py
│   │   └── post.py
│   │
│   ├── services/              # Business logic layer
│   │   ├── user_service.py    # User operations across DBs
│   │   ├── group_service.py   # Group coordination
│   │   ├── post_service.py    # Content management
│   │   └── recommendation_service.py  # Graph queries
│   │
│   ├── routers/               # API endpoints
│   │   ├── users.py
│   │   ├── groups.py
│   │   ├── posts.py
│   │   └── recommendations.py
│   │
│   └── tests/
│       └── test_services.py   # Unit tests with mocks
│
└── docker/
    └── init/
        ├── postgres-init.sql  # PostgreSQL schema
        └── seed.py            # Demo data seeding script
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB RAM recommended

### Run the Application

```bash
# Clone or navigate to project directory
cd campusconnect

# Start all services (databases + backend)
docker-compose up --build

# Wait for all services to be healthy and seed data to load
# You'll see "Seed completed successfully!" when ready

# The API will be available at:
# - API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
# - Neo4j Browser: http://localhost:7474 (neo4j/campus_pass_123)
```

### Verify Health

```bash
curl http://localhost:8000/health
```

---

## API Endpoints

### Users (PostgreSQL + Neo4j + Redis)

**1. Create User**
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@university.edu",
    "full_name": "New User"
  }'
```

**2. Get User Profile**
```bash
curl http://localhost:8000/users/1
```

**3. Add Friend**
```bash
curl -X POST http://localhost:8000/users/1/friends/2
```

### Groups (Multi-DB Coordination)

**4. Create Group**
```bash
curl -X POST http://localhost:8000/groups \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Advanced Databases Study Group",
    "course_code": "CS-450"
  }'
```

**5. Join Group**
```bash
curl -X POST http://localhost:8000/groups/1/join \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "role": "member"
  }'
```

### Posts (MongoDB + Redis)

**6. Create Post**
```bash
curl -X POST http://localhost:8000/groups/1/posts \
  -H "Content-Type: application/json" \
  -d '{
    "author_id": 1,
    "type": "question",
    "title": "What is polyglot persistence?",
    "body": "Can someone explain the benefits and tradeoffs?",
    "tags": ["databases", "architecture"]
  }'
```

**7. Get Group Feed**
```bash
curl "http://localhost:8000/groups/1/posts/feed?limit=10"
```

### Recommendations (Neo4j Graph Queries)

**8. Friend Recommendations**
```bash
curl http://localhost:8000/recommendations/users/1/friends
```

**9. Group Recommendations**
```bash
curl http://localhost:8000/recommendations/users/1/groups
```

**10. Leaderboard (Redis Sorted Sets)**
```bash
curl http://localhost:8000/recommendations/leaderboard
```

---

## Database Schemas

### PostgreSQL (Normalized Relational)

```sql
-- Source of truth for users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Study groups
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    course_code VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many relationship
CREATE TABLE group_memberships (
    user_id INTEGER REFERENCES users(id),
    group_id INTEGER REFERENCES groups(id),
    role VARCHAR(50) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id)
);
```

### MongoDB (Flexible Documents)

```javascript
// Posts collection - flexible schema for different content types
{
  _id: ObjectId("..."),
  author_id: 1,
  group_id: 1,
  type: "resource",  // "question" | "note" | "resource"
  title: "Great Tutorial",
  body: "Check this out...",
  tags: ["tutorial", "mongodb"],
  attachments: [
    {
      type: "link",
      url: "https://example.com/tutorial",
      title: "MongoDB Tutorial"
    }
  ],
  created_at: ISODate("2024-01-15T10:30:00Z"),
  updated_at: ISODate("2024-01-15T10:30:00Z")
}

// Comments collection
{
  _id: ObjectId("..."),
  post_id: ObjectId("..."),
  author_id: 2,
  body: "Great resource!",
  created_at: ISODate("2024-01-15T11:00:00Z")
}
```

### Neo4j (Graph Relationships)

```cypher
// User nodes
(:User {id: 1, email: "alice@university.edu", full_name: "Alice Johnson"})

// Group nodes
(:Group {id: 1, name: "Database Systems Study Group", course_code: "CS-401"})

// Relationships
(:User {id: 1})-[:FRIEND]->(:User {id: 2})
(:User {id: 1})-[:MEMBER_OF {role: "admin"}]->(:Group {id: 1})
```

### Redis (Key-Value Patterns)

```
# User cache (String with TTL)
user:1 -> JSON {id: 1, email: "...", full_name: "..."}  [TTL: 3600s]

# Group cache (String with TTL)
group:1 -> JSON {id: 1, name: "...", member_count: 5, post_count: 12}

# Leaderboard (Sorted Set)
leaderboard:points -> {
  "1": 150,   # user_id: score
  "2": 120,
  "3": 95
}

# Recent activity (List)
recent:group:1 -> [
  JSON {type: "post", user_id: 1, timestamp: "..."},
  JSON {type: "join", user_id: 3, timestamp: "..."}
]

# Hot posts (Sorted Set with timestamp scores)
hot:posts -> {
  "post_id_123": 1705327800.0,  # timestamp as score
  "post_id_456": 1705327750.0
}

# Rate limiting (String with TTL)
ratelimit:user:1 -> "45"  [TTL: 60s]
```

---

## Teaching Guide

This project is designed for classroom use to teach database design tradeoffs.

### Learning Objectives

1. **Understand polyglot persistence**: When and why to use multiple databases
2. **Recognize access patterns**: Match data patterns to database strengths
3. **Compare query complexity**: See real SQL vs Cypher vs document queries
4. **Learn caching strategies**: Implement cache-aside pattern with Redis
5. **Handle data consistency**: Coordinate writes across multiple systems

---

### Classroom Exercise 1: Performance Comparison

**Goal:** Demonstrate performance differences between databases for different queries.

**Setup:**
1. Ensure application is running with seeded data
2. Use Neo4j browser (http://localhost:7474) and PostgreSQL client

**Exercise:**

**Part A: Friend Recommendations**

Try this query in Neo4j Browser:
```cypher
// Friend-of-friend recommendations (simple, fast)
MATCH (me:User {id: 1})-[:FRIEND]->(friend)-[:FRIEND]->(fof:User)
WHERE me <> fof AND NOT (me)-[:FRIEND]->(fof)
WITH fof, COUNT(DISTINCT friend) as mutual_friends
ORDER BY mutual_friends DESC
LIMIT 10
RETURN fof.full_name, mutual_friends
```

Now try the SQL equivalent in PostgreSQL:
```sql
-- This is complex and slow even with indexes
SELECT u3.id, u3.full_name, COUNT(DISTINCT u2.id) as mutual_friends
FROM users u1
-- [complex joins as shown above]
```

**Questions:**
- How many lines of code? (Cypher: 6, SQL: 12+)
- Which is more readable?
- Run `EXPLAIN ANALYZE` - compare execution plans
- What happens with 10,000 users? 100,000?

**Part B: Leaderboard Updates**

Use Redis CLI:
```bash
docker exec -it campusconnect-redis redis-cli

# Time 1000 updates
TIME ZINCRBY leaderboard:points 1 user:1
# Typical result: < 1ms per operation

# Get top 10
TIME ZREVRANGE leaderboard:points 0 9 WITHSCORES
# Typical result: < 1ms
```

Compare to PostgreSQL:
```sql
-- Each update requires ORDER BY scan
UPDATE user_points SET points = points + 1 WHERE user_id = 1;
SELECT user_id, points FROM user_points ORDER BY points DESC LIMIT 10;
-- Much slower, especially with millions of rows
```

**Discussion:**
- Why is Redis faster for leaderboards?
- What are the tradeoffs? (Redis is in-memory, PostgreSQL is durable)
- When would you choose each approach?

---

### Classroom Exercise 2: Failure Mode Demonstration

**Goal:** Show what happens when each database becomes unavailable.

**Setup:**
```bash
# Application is running normally
curl http://localhost:8000/health  # All services healthy
```

**Exercise:**

**Scenario 1: Disable Redis (Cache Layer)**

```bash
# Stop Redis
docker stop campusconnect-redis

# Try getting user profile
curl http://localhost:8000/users/1

# What happens?
# - Slower response (cache miss, PostgreSQL fallback)
# - Still works! (graceful degradation)
# - Leaderboard fails (no fallback for Redis-only features)

# Restart Redis
docker start campusconnect-redis
```

**Scenario 2: Disable Neo4j (Graph Layer)**

```bash
# Stop Neo4j
docker stop campusconnect-neo4j

# Try recommendations
curl http://localhost:8000/recommendations/users/1/friends

# What happens?
# - Recommendations fail (Neo4j is only source)
# - Other features still work (users, groups, posts)

# Restart Neo4j
docker start campusconnect-neo4j
```

**Scenario 3: Disable MongoDB (Content Layer)**

```bash
# Stop MongoDB
docker stop campusconnect-mongodb

# Try getting group feed
curl "http://localhost:8000/groups/1/posts/feed"

# What happens?
# - Posts unavailable
# - User/group management still works

# Restart MongoDB
docker start campusconnect-mongodb
```
---

### Classroom Exercise 3: Modify Recommendation Query

**Goal:** Hands-on experience writing Neo4j Cypher queries.

**Task:** Modify the friend recommendation algorithm to include different criteria.

**Current Implementation** ([backend/db/neo4j.py:112](backend/db/neo4j.py#L112)):

```cypher
MATCH (me:User {id: $user_id})-[:FRIEND]->(friend)-[:FRIEND]->(fof:User)
WHERE me <> fof AND NOT (me)-[:FRIEND]->(fof)
WITH fof, COUNT(DISTINCT friend) as mutual_friends
ORDER BY mutual_friends DESC
LIMIT $limit
RETURN fof.id, fof.full_name, mutual_friends
```

**Modifications to Try:**

**Option 1: Recommend friends who share groups**
```cypher
MATCH (me:User {id: $user_id})-[:MEMBER_OF]->(g:Group)<-[:MEMBER_OF]-(other:User)
WHERE me <> other AND NOT (me)-[:FRIEND]->(other)
WITH other, COUNT(DISTINCT g) as common_groups
ORDER BY common_groups DESC
LIMIT $limit
RETURN other.id, other.full_name, common_groups
```

**Option 2: Combined score (friends + groups)**
```cypher
MATCH (me:User {id: $user_id})
MATCH (me)-[:FRIEND]->(friend)-[:FRIEND]->(fof:User)
WHERE me <> fof AND NOT (me)-[:FRIEND]->(fof)
WITH me, fof, COUNT(DISTINCT friend) as mutual_friends

OPTIONAL MATCH (me)-[:MEMBER_OF]->(g:Group)<-[:MEMBER_OF]-(fof)
WITH fof, mutual_friends, COUNT(DISTINCT g) as common_groups

WITH fof, mutual_friends, common_groups,
     (mutual_friends * 2 + common_groups) as score
ORDER BY score DESC
LIMIT $limit
RETURN fof.id, fof.full_name, mutual_friends, common_groups, score
```

**Steps:**
1. Open [backend/db/neo4j.py:112](backend/db/neo4j.py#L112)
2. Replace the Cypher query in `recommend_friends` method
3. Restart the backend container:
   ```bash
   docker-compose restart backend
   ```
4. Test the new recommendations:
   ```bash
   curl http://localhost:8000/recommendations/users/1/friends
   ```

**Discussion:**
- How does the ranking change?
- Which approach gives better recommendations?
- What's the performance impact of `OPTIONAL MATCH`?
- How would you test this in production?

---

## Running Tests

```bash
# Run unit tests
docker exec -it campusconnect-backend pytest backend/tests/test_services.py -v

# Run with coverage
docker exec -it campusconnect-backend pytest backend/tests/ --cov=backend --cov-report=term-missing
```

**What the tests demonstrate:**
- Mocking multiple database clients
- Testing cache-aside pattern
- Testing coordinated multi-database writes
- Testing cross-database enrichment

---

## Common Issues & Troubleshooting

**Issue: "Connection refused" errors on startup**
- **Cause:** Databases not ready yet
- **Solution:** Wait 30-60 seconds for health checks to pass

**Issue: "User is not a member of this group" when creating posts**
- **Cause:** Need to join group first
- **Solution:** Use endpoint #5 to join before creating posts

**Issue: Neo4j browser shows no data**
- **Cause:** Seed script hasn't run yet
- **Solution:** Check backend logs for "Seed completed successfully!"

**Issue: Tests fail with connection errors**
- **Cause:** Tests use mocks, not real databases
- **Solution:** This is expected - tests don't require running databases

---

## Advanced Topics

### Adding a New Database

**Example: Adding Elasticsearch for full-text search**

1. Add to [docker-compose.yml](docker-compose.yml):
```yaml
elasticsearch:
  image: elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"
```

2. Create client: [backend/db/elasticsearch.py](backend/db/elasticsearch.py)
3. Index posts on creation in [backend/services/post_service.py:35](backend/services/post_service.py#L35)
4. Add search endpoint in [backend/routers/posts.py](backend/routers/posts.py)

### Eventual Consistency Considerations

This demo assumes synchronous writes. In production:

- Use message queues (RabbitMQ, Kafka) for async propagation
- Implement compensating transactions for failures
- Add idempotency keys for retries
- Monitor lag between databases

---

## Key Takeaways

✅ **Use the right tool for the job** - Each database solves specific problems
✅ **PostgreSQL for relational data** - ACID, integrity, authoritative records
✅ **Redis for speed** - Caching, leaderboards, real-time features
✅ **MongoDB for flexibility** - Evolving schemas, nested documents
✅ **Neo4j for relationships** - Social graphs, recommendations, pattern matching

⚠️ **Tradeoffs:**
- More complexity (multiple systems to manage)
- Eventual consistency challenges
- Higher operational overhead
- Need for careful data modeling

🎓 **When NOT to use polyglot persistence:**
- Simple CRUD apps (PostgreSQL alone is fine)
- Small scale (< 10K users)
- Limited team expertise
- Strict consistency requirements across all data

---

## License

MIT License - Free to use for education and learning

---
