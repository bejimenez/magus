# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Magus API"
    version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./name_generator.db"

    # generation settings
    max_name_length: int = 15
    min_name_length: int = 2
    default_count: int = 1
    max_count: int = 20

    cache_ttl: int = 3600
    use_redis: bool = False # for now
    redis_url: str = "redis://localhost:6379"

    max_syllables: int = 5
    min_score_threshold: float = 0.6

    class Config: 
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
