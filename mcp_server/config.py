"""
Configuration module for OpenEdge Analytics MCP Server.

Loads settings from environment variables (.env file).
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


# Load .env file from project root
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    dsn: str
    user: Optional[str]
    password: Optional[str]
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create DatabaseConfig from environment variables."""
        return cls(
            dsn=os.getenv("ODBC_DSN", "QAD_OPENEDGE_ANALYTICS"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            timeout_seconds=int(os.getenv("DB_TIMEOUT_SECONDS", "30")),
        )


@dataclass
class AppConfig:
    """Application configuration."""

    database: DatabaseConfig
    # Analytics Mart 스키마 이름 - 필요시 여기서만 수정하면 됨
    analytics_schema: str = "ANALYTICS_MART"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create AppConfig from environment variables."""
        return cls(
            database=DatabaseConfig.from_env(),
            analytics_schema=os.getenv("ANALYTICS_SCHEMA", "ANALYTICS_MART"),
        )


# Global config instance
config = AppConfig.from_env()


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return config


def get_sql_template_path(template_name: str) -> Path:
    """
    Get the full path to a SQL template file.

    Args:
        template_name: Name of the SQL template file (e.g., 'oee_trend.sql')

    Returns:
        Path to the SQL template file.
    """
    return Path(__file__).parent.parent / "sql_templates" / template_name


def load_sql_template(template_name: str) -> str:
    """
    Load a SQL template file content.

    Args:
        template_name: Name of the SQL template file (e.g., 'oee_trend.sql')

    Returns:
        SQL template string content.

    Raises:
        FileNotFoundError: If template file does not exist.
    """
    template_path = get_sql_template_path(template_name)
    if not template_path.exists():
        raise FileNotFoundError(f"SQL template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")
