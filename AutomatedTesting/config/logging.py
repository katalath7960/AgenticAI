"""Logging configuration for the pipeline."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("autotester")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)
    return logger
