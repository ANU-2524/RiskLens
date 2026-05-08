"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """RiskLens application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "RiskLens — Risk Intelligence Platform"
    environment: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://RiskLens:RiskLens@localhost:5432/RiskLens_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Claude API
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-5-sonnet-20241022"
    claude_max_tokens: int = 2000
    claude_rate_limit_per_hour: int = 50

    # Market Data
    alpha_vantage_api_key: str = ""

    # Qdrant Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "RiskLens_signals"
    embedding_model: str = "all-MiniLM-L6-v2"

    # CORS
    cors_origins: List[str] = ["http://localhost:5155", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | List[str]) -> List[str]:
        """Parse comma-separated CORS origins string."""
        if isinstance(v, str):
            if not v or v.strip() == "":
                return ["http://localhost:5155", "http://localhost:3000"]
            return [origin.strip() for origin in v.split(",")]
        return v

    # Rate limiting
    rate_limit_per_minute: int = 100

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Cache TTLs (seconds)
    cache_ttl_risk_scores: int = 300   # 5 minutes
    cache_ttl_live_alerts: int = 60    # 1 minute

    # Risk scoring thresholds
    risk_threshold_high: float = 60.0
    risk_threshold_critical: float = 80.0
    anomaly_std_threshold: float = 2.0


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()

