"""Structured logging configuration."""

from __future__ import annotations

import json
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

from .config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()

    # Create logs directory
    log_dir = settings.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    log_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "text": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": JSONFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": settings.log_format,
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": settings.log_format,
                "filename": log_dir / "taxbot.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "scraper": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": settings.log_format,
                "filename": log_dir / "scraper.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "api": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": settings.log_format,
                "filename": log_dir / "api.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "taxbot": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "taxbot.scrapers": {
                "level": settings.log_level,
                "handlers": ["console", "scraper"],
                "propagate": False,
            },
            "taxbot.api": {
                "level": settings.log_level,
                "handlers": ["console", "api"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "api"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(log_config)


def get_logger(name: str) -> logging.Logger:
    """Get logger for the given name."""
    return logging.getLogger(f"taxbot.{name}")


def get_scraper_logger() -> logging.Logger:
    """Get scraper-specific logger."""
    return get_logger("scrapers")


def get_api_logger() -> logging.Logger:
    """Get API-specific logger."""
    return get_logger("api")
