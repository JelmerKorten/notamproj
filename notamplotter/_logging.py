"""Centralised logging setup for NotamPlotter.

All modules should obtain their logger via ``get_logger`` and only the
application entry points should call :func:`setup_logging`.  This keeps a
single source of truth for the logging configuration (see AGENT_PLAN.md,
Phase 1: "Consolidate logging").
"""

import logging

LOG_FILE = "plotter.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.DEBUG, filename: str = LOG_FILE) -> None:
    """Configure the root logger.  Idempotent; safe to call from every entry point."""
    logging.basicConfig(
        level=level,
        filename=filename,
        filemode="a",
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger."""
    return logging.getLogger(name)
