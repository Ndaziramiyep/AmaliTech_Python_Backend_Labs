"""Single source of truth for runtime settings, read from the environment after loading a .env file from the current directory (if present) so local overrides don't need to be exported manually."""
import os
from dataclasses import dataclass
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()



@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable bundle of resolved runtime settings for Postgres, Redis, and Mongo."""

    postgres_dsn: str
    postgres_pool_min_size: int
    postgres_pool_max_size: int
    redis_url: str
    redis_timeline_ttl_seconds: int
    mongo_uri: str
    mongo_db_name: str


def _build_postgres_dsn() -> str:
    """Build a Postgres connection string from environment variables set in .env."""
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    database = os.environ["POSTGRES_DB"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


def load_settings() -> Settings:
    """Read all runtime settings from the environment and return them as a `Settings` instance."""
    return Settings(
        postgres_dsn=_build_postgres_dsn(),
        postgres_pool_min_size=int(os.environ["POSTGRES_POOL_MIN_SIZE"]),
        postgres_pool_max_size=int(os.environ["POSTGRES_POOL_MAX_SIZE"]),
        redis_url=os.environ["REDIS_URL"],
        redis_timeline_ttl_seconds=int(os.environ["REDIS_TIMELINE_TTL_SECONDS"]),
        mongo_uri=os.environ["MONGO_URI"],
        mongo_db_name=os.environ["MONGO_DB_NAME"],
    )
