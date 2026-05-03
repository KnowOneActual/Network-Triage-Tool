"""Configuration management for Network Triage Tool.

Uses pydantic-settings to manage application settings via environment variables
and configuration files.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for Network Triage Tool."""

    # App Info
    app_name: str = "Network Triage Tool"
    version: str = "0.5.9"
    debug: bool = False

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

    # Network Defaults
    default_timeout: int = Field(default=5, ge=1, le=30)
    max_workers: int = Field(default=20, ge=1, le=100)

    # DNS Settings
    dns_cache_ttl: int = Field(default=300, ge=0)

    # Port Scanner Settings
    port_scan_timeout: int = Field(default=3, ge=1, le=10)

    # Latency Settings
    ping_count: int = Field(default=4, ge=1, le=20)
    ping_timeout: int = Field(default=2, ge=1, le=10)

    model_config = SettingsConfigDict(
        env_prefix="NTT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the current settings instance."""
    return settings
