# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Application settings and configuration
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # API Keys
    anthropic_api_key: str = Field(default="")
    market_data_api_key: str = Field(default="")
    market_data_provider: str = Field(default="polygon")

    # Database
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/options_db")
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    redis_db: int = Field(default=0)

    # ML Models
    model_path: str = Field(default="./models")
    retrain_interval_hours: int = Field(default=24)

    # Trading Parameters
    max_position_size: float = Field(default=0.05)
    confidence_threshold: float = Field(default=0.7)
    min_liquidity: int = Field(default=1000)

    # Risk Management
    max_loss_per_trade: float = Field(default=0.02)
    max_daily_trades: int = Field(default=10)

    # Claude API
    claude_model: str = Field(default="claude-sonnet-4-5-20250929")
    claude_max_tokens: int = Field(default=1024)
    claude_temperature: float = Field(default=0.7)

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
