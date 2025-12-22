# CampusConnect - Common Commands Reference

Quick reference for frequently used commands.

## Docker Compose Commands

```bash
# Start all services
docker-compose up

# Start in background (detached mode)
docker-compose up -d

# Build and start
docker-compose up --build

# Stop all services
docker-compose down

# Stop and remove volumes (DELETE ALL DATA)
docker-compose down -v

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis

# Restart a service
docker-compose restart backend

# Check service status
docker-compose ps
```

## Makefile Commands

```bash
# Start services
make up

# Stop services
make down

# View logs
make logs

# Check health
make health

# Run tests
make test

# Re-run seed script
make seed

# Open API docs
make docs

# Clean everything (delete data)
make clean

# Build containers
make build
```

## API Testing Commands

```bash
# Health check
curl http://localhost:8000/health

# Run all examples
bash API_EXAMPLES.sh

# Create user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@uni.edu","full_name":"Test User"}'

# Get user profile
curl http://localhost:8000/users/1

# Friend recommendations
curl http://localhost:8000/recommendations/users/1/friends

# Group recommendations
curl http://localhost:8000/recommendations/users/1/groups

# Leaderboard
curl http://localhost:8000/recommendations/leaderboard

# Group feed
curl http://localhost:8000/groups/1/posts/feed?limit=10
```

## Database Access Commands

### PostgreSQL
```bash
# Connect to PostgreSQL
docker exec -it campusconnect-postgres psql -U campus_admin -d campusconnect

# Common queries
SELECT * FROM users;
SELECT * FROM groups;
SELECT * FROM group_memberships;
SELECT u.full_name, g.name, gm.role
FROM users u
JOIN group_memberships gm ON u.id = gm.user_id
JOIN groups g ON gm.group_id = g.id;

# Exit: \q
```

### Redis
```bash
# Connect to Redis CLI
docker exec -it campusconnect-redis redis-cli

# Common commands
KEYS *                                      # List all keys
GET user:1                                  # Get cached user
ZREVRANGE leaderboard:points 0 9 WITHSCORES # Top 10 leaderboard
LRANGE recent:group:1 0 9                   # Recent activity
ZRANGE hot:posts 0 9                        # Hot posts
TTL user:1                                  # Time to live

# Exit: exit
```

### MongoDB
```bash
# Connect to MongoDB shell
docker exec -it campusconnect-mongodb mongosh \
  -u campus_admin -p campus_pass_123 campusconnect

# Common queries
db.posts.find().pretty()                    # All posts
db.posts.countDocuments()                   # Count posts
db.posts.find({group_id: 1}).pretty()       # Posts in group 1
db.posts.find({tags: "databases"}).pretty() # Posts with tag
db.comments.find().pretty()                 # All comments

# Exit: exit
```

### Neo4j
```bash
# Open Neo4j Browser
open http://localhost:7474
# Login: neo4j / campus_pass_123

# Common Cypher queries
MATCH (n) RETURN n LIMIT 25;                          // All nodes

MATCH (u:User) RETURN u;                              // All users

MATCH (u:User)-[r:FRIEND]->(f:User) RETURN u, r, f;  // Friendships

MATCH (u:User)-[:MEMBER_OF]->(g:Group) RETURN u, g;  // Memberships

// Friend-of-friend recommendations
MATCH (me:User {id: 1})-[:FRIEND]->(friend)-[:FRIEND]->(fof:User)
WHERE me <> fof AND NOT (me)-[:FRIEND]->(fof)
WITH fof, COUNT(friend) as mutual
RETURN fof.full_name, mutual
ORDER BY mutual DESC;

// Groups with most members
MATCH (u:User)-[:MEMBER_OF]->(g:Group)
WITH g, COUNT(u) as members
RETURN g.name, members
ORDER BY members DESC;
```

## Testing Commands

```bash
# Run all tests
docker exec -it campusconnect-backend pytest backend/tests/ -v

# Run specific test file
docker exec -it campusconnect-backend pytest backend/tests/test_services.py -v

# Run with coverage
docker exec -it campusconnect-backend pytest backend/tests/ --cov=backend

# Run specific test
docker exec -it campusconnect-backend pytest backend/tests/test_services.py::TestUserService::test_create_user_writes_to_all_databases -v
```

## Development Commands

```bash
# Rebuild backend only
docker-compose up --build backend

# Enter backend container shell
docker exec -it campusconnect-backend /bin/bash

# View backend logs
docker-compose logs -f backend

# Restart backend after code changes
docker-compose restart backend

# Check Python syntax
docker exec -it campusconnect-backend python -m py_compile backend/main.py
```

## Debugging Commands

```bash
# Check which ports are in use
lsof -i :8000
lsof -i :5432
lsof -i :6379
lsof -i :27017
lsof -i :7474

# Check container status
docker ps -a

# Check container resource usage
docker stats

# Inspect container
docker inspect campusconnect-backend

# Check container logs
docker logs campusconnect-backend
docker logs campusconnect-postgres
docker logs campusconnect-redis
docker logs campusconnect-mongodb
docker logs campusconnect-neo4j

# Check network
docker network ls
docker network inspect multidb_default
```

## Data Management

```bash
# Re-seed database (keeps existing data)
docker exec -it campusconnect-backend python /app/docker/init/seed.py

# Backup PostgreSQL
docker exec campusconnect-postgres pg_dump -U campus_admin campusconnect > backup.sql

# Restore PostgreSQL
cat backup.sql | docker exec -i campusconnect-postgres psql -U campus_admin campusconnect

# Export MongoDB collection
docker exec campusconnect-mongodb mongoexport \
  -u campus_admin -p campus_pass_123 \
  -d campusconnect -c posts --out=/tmp/posts.json

# Clear Redis cache
docker exec -it campusconnect-redis redis-cli FLUSHALL
```

## Verification Commands

```bash
# Verify project structure
bash verify_project.sh

# Check health of all services
curl http://localhost:8000/health | python3 -m json.tool

# Test each database individually
docker exec campusconnect-postgres psql -U campus_admin -c "SELECT 1"
docker exec campusconnect-redis redis-cli PING
docker exec campusconnect-mongodb mongosh --eval "db.runCommand({ping:1})"
curl http://localhost:7474 -I

# Count records in each database
docker exec campusconnect-postgres psql -U campus_admin campusconnect -c "SELECT COUNT(*) FROM users;"
docker exec campusconnect-redis redis-cli DBSIZE
docker exec campusconnect-mongodb mongosh -u campus_admin -p campus_pass_123 campusconnect --eval "db.posts.countDocuments()"
```

## Performance Testing

```bash
# Benchmark API endpoint
ab -n 100 -c 10 http://localhost:8000/users/1

# Or with Apache Bench alternative
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/users/1

# Create curl-format.txt:
echo "time_namelookup: %{time_namelookup}\ntime_connect: %{time_connect}\ntime_starttransfer: %{time_starttransfer}\ntime_total: %{time_total}\n" > curl-format.txt
```

## Cleanup Commands

```bash
# Remove all containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove unused Docker resources
docker system prune

# Remove all project containers and images
docker-compose down --rmi all -v

# Start fresh
make clean && make build && make up
```

## Useful Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
alias cup='docker-compose up'
alias cdown='docker-compose down'
alias clogs='docker-compose logs -f'
alias cps='docker-compose ps'

alias cc-health='curl http://localhost:8000/health | python3 -m json.tool'
alias cc-docs='open http://localhost:8000/docs'
alias cc-test='docker exec -it campusconnect-backend pytest backend/tests/ -v'
```

## Quick Troubleshooting

```bash
# Service won't start
docker-compose down -v && docker-compose up --build

# Connection refused errors
docker-compose ps  # Check all services are running
make health        # Check health status
docker-compose logs [service_name]  # Check specific logs

# Out of memory
docker system prune -a  # Clean up unused resources
# Increase Docker memory in Docker Desktop settings

# Port already in use
docker-compose down
lsof -ti:8000 | xargs kill -9  # Kill process using port
docker-compose up

# Seed data issues
docker exec -it campusconnect-backend python /app/docker/init/seed.py
```

---

For more help, see:
- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [API_EXAMPLES.sh](API_EXAMPLES.sh) - Complete API examples
