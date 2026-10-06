"""
Structured and contextual logging configuration for the university assistant.
Provides clean console output with timestamps, severity levels, and optional trace IDs.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str = "university_assistant") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger("app")
