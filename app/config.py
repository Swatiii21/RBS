"""Centralized Configuration Module for Restaurant Billing System.

TQM Quality Goal: Q11 - Improve Maintainability
Student: Swati Melkani (CSE - B, 2026-27)
Course: BBAT104 - Fundamentals of Total Quality Management

This module defines configuration classes for development, testing, and production.
It loads variables from the environment (.env) with validated fallbacks, avoiding
hardcoded values and ensuring clear separation between technical environment
configuration and editable business settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


# Base workspace directory (where run.py resides)
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Base configuration with sensible defaults."""

    # Project metadata
    STUDENT_NAME: str = "Swati Melkani"
    STUDENT_BRANCH: str = "CSE - Section B"
    COURSE_NAME: str = "BBAT104 — Fundamentals of Total Quality Management"
    ACADEMIC_SESSION: str = "2026–27"
    ASSIGNED_GOAL: str = "Q11 — Improve Maintainability"

    # Application identity
    APP_NAME: str = os.getenv("APP_NAME", "Restaurant Billing System — Q11")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_insecure_key_for_local_demonstration_only")

    # Paths
    BASE_DIR: Path = BASE_DIR
    INSTANCE_DIR: Path = BASE_DIR / "instance"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Database
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH", str(BASE_DIR / "instance" / "restaurant.db")
    )

    # Diagnostic Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE: str = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", 1048576))  # 1 MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", 5))

    # Business Defaults (Editable via UI System Settings stored in DB)
    DEFAULT_CURRENCY: str = "₹"
    DEFAULT_TAX_RATE: float = 5.0
    MAX_DISCOUNT_PERCENT: float = 25.0
    DEFAULT_PAGE_SIZE: int = 15

    # Server settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 5000))
    TESTING: bool = False
    DEBUG: bool = False

    @classmethod
    def validate(cls) -> None:
        """Validate startup configuration to prevent runtime failures.

        Raises:
            ValueError: If any critical configuration parameter is invalid.
        """
        # Ensure directories exist
        cls.INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Validate log level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if cls.LOG_LEVEL not in valid_log_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL '{cls.LOG_LEVEL}'. Must be one of {valid_log_levels}"
            )

        # Validate numeric bounds
        if cls.DEFAULT_TAX_RATE < 0 or cls.DEFAULT_TAX_RATE > 100:
            raise ValueError(
                f"DEFAULT_TAX_RATE must be between 0 and 100, got {cls.DEFAULT_TAX_RATE}"
            )

        if cls.MAX_DISCOUNT_PERCENT < 0 or cls.MAX_DISCOUNT_PERCENT > 100:
            raise ValueError(
                f"MAX_DISCOUNT_PERCENT must be between 0 and 100, got {cls.MAX_DISCOUNT_PERCENT}"
            )


class DevelopmentConfig(Config):
    """Configuration for local development and academic evaluation."""

    DEBUG: bool = True
    FLASK_ENV: str = "development"


class TestingConfig(Config):
    """Isolated configuration for automated pytest runs."""

    TESTING: bool = True
    DEBUG: bool = False
    # Isolated test database file
    DATABASE_PATH: str = str(BASE_DIR / "instance" / "test_restaurant.db")
    LOG_LEVEL: str = "WARNING"


class ProductionConfig(Config):
    """Configuration placeholder for production deployment."""

    DEBUG: bool = False
    TESTING: bool = False


# Map of configuration environment names to classes
CONFIG_MAP: Dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name: str | None = None) -> type[Config]:
    """Retrieve and validate the application configuration.

    Args:
        env_name: Name of environment ('development', 'testing', 'production').
                  Defaults to the FLASK_ENV environment variable.

    Returns:
        Config class corresponding to the requested environment.
    """
    if env_name is None:
        env_name = os.getenv("FLASK_ENV", "development").lower()

    config_class = CONFIG_MAP.get(env_name, DevelopmentConfig)
    config_class.validate()
    return config_class
