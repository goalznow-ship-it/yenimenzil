"""Structured logging and observability for YeniMenzil.az."""

import logging
import os
import sys

from pythonjsonlogger import jsonlogger


def setup_structured_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured JSON logging for production observability.

    Returns the root logger for convenience.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Avoid adding handlers if already configured
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)

    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(process)d %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(log_level)

    # Log startup message with environment info
    logger.info(
        "structured_logging_initialized",
        extra={
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "environment": os.getenv("APP_ENV", "development"),
        },
    )

    return logger


# Auto-initialize in production if requested via environment
if os.getenv("APP_ENV", "development") == "production":
    _logger = setup_structured_logging(os.getenv("LOG_LEVEL", "INFO"))