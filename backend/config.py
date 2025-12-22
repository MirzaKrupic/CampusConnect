"""
Configuration management for CampusConnect
Loads settings from environment variables
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "campusconnect")
    postgres_user: str = os.getenv("POSTGRES_USER", "campus_admin")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "campus_pass_123")

    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))

    # MongoDB
    mongodb_host: str = os.getenv("MONGODB_HOST", "localhost")
    mongodb_port: int = int(os.getenv("MONGODB_PORT", "27017"))
    mongodb_db: str = os.getenv("MONGODB_DB", "campusconnect")
    mongodb_user: str = os.getenv("MONGODB_USER", "campus_admin")
    mongodb_password: str = os.getenv("MONGODB_PASSWORD", "campus_pass_123")

    # Neo4j
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "campus_pass_123")

    # Application
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def postgres_dsn(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def mongodb_uri(self) -> str:
        return f"mongodb://{self.mongodb_user}:{self.mongodb_password}@{self.mongodb_host}:{self.mongodb_port}"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
