"""Logging configuration for Network Triage Tool.

Implements structured logging using structlog.
"""

import logging
import sys
from typing import Any, cast

import structlog


def configure_logging(level: int = logging.INFO, json_format: bool = False) -> None:
    """Configure structured logging.

    Args:
        level: Logging level (default: logging.INFO)
        json_format: Whether to output in JSON format (default: False)

    """
    shared_processors: list[Any] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger.

    Args:
        name: Logger name

    Returns:
        BoundLogger instance

    """
    return cast("structlog.stdlib.BoundLogger", structlog.get_logger(name))
