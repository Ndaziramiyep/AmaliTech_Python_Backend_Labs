"""Single source of truth for runtime settings, read from the environment."""
import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    postgres_dsn: str
    postgres_pool_min_size: int
    postgres_pool_max_size: int
    redis_url: str
    redis_timeline_ttl_seconds: int
    mongo_uri: str
    mongo_db_name: str


def load_settings() -> Settings:
    return Settings(
        postgres_dsn=os.environ.get(
            "POSTGRES_DSN", "postgresql://social:social@localhost:5433/social"
        ),
        postgres_pool_min_size=int(os.environ.get("POSTGRES_POOL_MIN_SIZE", "1")),
        postgres_pool_max_size=int(os.environ.get("POSTGRES_POOL_MAX_SIZE", "10")),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6380/0"),
        redis_timeline_ttl_seconds=int(
            os.environ.get("REDIS_TIMELINE_TTL_SECONDS", "60")
        ),
        mongo_uri=os.environ.get("MONGO_URI", "mongodb://localhost:27018"),
        mongo_db_name=os.environ.get("MONGO_DB_NAME", "social_activity"),
    )
