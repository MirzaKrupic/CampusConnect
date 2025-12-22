"""
CampusConnect - Polyglot Persistence Demo Application
FastAPI application demonstrating multiple database patterns
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from backend.db.postgres import postgres_client
from backend.db.redis import redis_client
from backend.db.mongo import mongo_client
from backend.db.neo4j import neo4j_client

from backend.routers import users, groups, posts, recommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    Connect to all databases on startup, disconnect on shutdown
    """
    # Startup
    logger.info("Starting CampusConnect application...")

    try:
        logger.info("Connecting to PostgreSQL...")
        await postgres_client.connect()

        logger.info("Connecting to Redis...")
        await redis_client.connect()

        logger.info("Connecting to MongoDB...")
        await mongo_client.connect()

        logger.info("Connecting to Neo4j...")
        await neo4j_client.connect()

        logger.info("All database connections established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to databases: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down CampusConnect application...")

    await postgres_client.disconnect()
    await redis_client.disconnect()
    await mongo_client.disconnect()
    await neo4j_client.disconnect()

    logger.info("All database connections closed")


app = FastAPI(
    title="CampusConnect API",
    description="Polyglot persistence demo: PostgreSQL + Redis + MongoDB + Neo4j",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(users.router)
app.include_router(groups.router)
app.include_router(posts.router)
app.include_router(recommendations.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CampusConnect API",
        "status": "running",
        "databases": {
            "postgresql": "System of record - users, groups, memberships",
            "redis": "Cache, leaderboards, rate limiting, activity streams",
            "mongodb": "Flexible content - posts, comments, attachments",
            "neo4j": "Graph relationships - friendships, recommendations",
        },
    }


@app.get("/health")
async def health_check():
    """Detailed health check for all databases"""
    health_status = {
        "status": "healthy",
        "databases": {}
    }

    # Check PostgreSQL
    try:
        async with postgres_client.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health_status["databases"]["postgresql"] = "healthy"
    except Exception as e:
        health_status["databases"]["postgresql"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        await redis_client.client.ping()
        health_status["databases"]["redis"] = "healthy"
    except Exception as e:
        health_status["databases"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check MongoDB
    try:
        await mongo_client.client.admin.command("ping")
        health_status["databases"]["mongodb"] = "healthy"
    except Exception as e:
        health_status["databases"]["mongodb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Neo4j
    try:
        async with neo4j_client.driver.session() as session:
            await session.run("RETURN 1")
        health_status["databases"]["neo4j"] = "healthy"
    except Exception as e:
        health_status["databases"]["neo4j"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
