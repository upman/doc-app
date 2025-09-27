"""
Environment configuration module for the FastAPI backend.
Handles different environments: development, production, test
"""
import os
from enum import Enum
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Environment(str, Enum):
    """Environment enumeration"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class Settings(BaseSettings):
    """Application settings that can be configured via environment variables"""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True

    # API Configuration
    api_title: str = "Document API"
    api_version: str = "1.0.0"
    api_description: str = "API for document management"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # CORS Configuration
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    # Database Configuration (for future use)
    database_url: Optional[str] = None
    database_name: str = "documents.db"

    # File Storage Configuration
    data_directory: str = "data"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list[str] = Field(default=[".pdf", ".doc", ".docx", ".txt", ".md"])

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30

    # Anthropic API Configuration
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key for Files API")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Environment-specific adjustments
        if self.environment == Environment.DEVELOPMENT:
            self.debug = True
            self.log_level = "DEBUG"
        elif self.environment == Environment.PRODUCTION:
            self.debug = False
            self.log_level = "INFO"
            if self.secret_key == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production environment")
        elif self.environment == Environment.TEST:
            self.debug = True
            self.log_level = "WARNING"
            self.data_directory = "test_data"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION

    @property
    def is_test(self) -> bool:
        """Check if running in test environment"""
        return self.environment == Environment.TEST

    @property
    def data_path(self) -> Path:
        """Get the absolute path to the data directory"""
        base_path = Path(__file__).parent.parent
        return base_path / self.data_directory

    def ensure_data_directory(self) -> None:
        """Ensure the data directory exists"""
        self.data_path.mkdir(exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    This function is cached to avoid re-reading environment variables multiple times.
    """
    return Settings()


# Global settings instance
settings = get_settings()