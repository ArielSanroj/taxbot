"""Configuration management using Pydantic Settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, EmailStr, Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "TaxBot Enterprise"
    app_version: str = "1.0.0"
    debug: bool = False

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")

    # Security
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    api_key: str = Field(..., env="API_KEY")

    # Ollama Configuration
    ollama_model: str = Field(default="llama3", env="OLLAMA_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_timeout: int = Field(default=300, env="OLLAMA_TIMEOUT")

    # Email Configuration
    email_sender: Optional[EmailStr] = Field(default=None, env="DIAN_EMAIL_SENDER")
    email_password: Optional[str] = Field(default=None, env="DIAN_EMAIL_PASSWORD")
    email_recipients: List[EmailStr] = Field(default_factory=list, env="DIAN_EMAIL_RECIPIENTS")
    email_smtp_host: str = Field(default="smtp.gmail.com", env="EMAIL_SMTP_HOST")
    email_smtp_port: int = Field(default=465, env="EMAIL_SMTP_PORT")
    email_smtp_use_tls: bool = Field(default=True, env="EMAIL_SMTP_USE_TLS")

    # Scraping Configuration
    scraper_delay: float = Field(default=1.0, env="SCRAPER_DELAY")
    scraper_timeout: int = Field(default=30, env="SCRAPER_TIMEOUT")
    scraper_retry_attempts: int = Field(default=3, env="SCRAPER_RETRY_ATTEMPTS")
    scraper_retry_delay: float = Field(default=5.0, env="SCRAPER_RETRY_DELAY")
    scraper_max_text_length: int = Field(default=12000, env="SCRAPER_MAX_TEXT_LENGTH")

    # Data Storage
    data_dir: Path = Field(default=Path("./data"), env="DATA_DIR")
    csv_backup_count: int = Field(default=5, env="CSV_BACKUP_COUNT")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="text", env="LOG_FORMAT")

    # Database (optional)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")

    @validator("email_recipients", pre=True)
    def parse_email_recipients(cls, v):
        """Parse comma-separated email recipients."""
        if isinstance(v, str):
            return [email.strip() for email in v.split(",") if email.strip()]
        return v

    @validator("data_dir", pre=True)
    def resolve_data_dir(cls, v):
        """Resolve data directory path."""
        if isinstance(v, str):
            return Path(v).resolve()
        return v.resolve()

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @validator("log_format")
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ["text", "json"]
        if v.lower() not in valid_formats:
            raise ValueError("Log format must be 'text' or 'json'")
        return v.lower()

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global settings
    settings = Settings()
    return settings
