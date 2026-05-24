"""
Structured logging configuration.

Two outputs:
1. Console → human-readable colored output (for developers)
2. File    → JSON lines format (for CI, log aggregation, debugging)

Log rotation:
- New file per day
- Max 10 files kept
- Old logs auto-deleted

Usage anywhere:
    from src.razorpay.utils.logger import logger
    logger.info("event_name", key1="value1", key2="value2")
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

import structlog


# ──────────────────────────────────────
# Log directory setup
# ──────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _get_log_filename() -> str:
    """
    Generate log filename with today's date.
    Each day gets its own log file.

    Example: logs/test_run_2024-01-15.log
    """
    today = datetime.now().strftime("%Y-%m-%d")
    return f"test_run_{today}.log"


def _create_file_handler() -> RotatingFileHandler:
    """
    Create a rotating file handler.

    Rotation rules:
    - Max 10 MB per file
    - Keep 10 backup files
    - After 10 files, oldest is deleted

    10 files × 10 MB = max 100 MB of logs ever.
    """
    log_file = LOG_DIR / _get_log_filename()

    handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,    # 10 MB
        backupCount=10,                # keep 10 old files
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)   # file gets EVERYTHING

    # JSON format for file (machine parseable)
    handler.setFormatter(
        logging.Formatter("%(message)s")   # structlog handles formatting
    )

    return handler


def _create_console_handler() -> logging.StreamHandler:
    """
    Create console handler.
    Shows colored human-readable output.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)   # console gets INFO and above

    handler.setFormatter(
        logging.Formatter("%(message)s")
    )

    return handler


def setup_logger() -> structlog.BoundLogger:
    """
    Configure structlog with dual output.

    Pipeline:
    1. Log call → structlog processors
    2. Processors add timestamp, level, etc.
    3. Output 1 → console (colored, human readable)
    4. Output 2 → file (JSON lines, machine readable)
    """

    # ── Step 1: Configure standard library logging ──
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers (avoid duplicates on re-import)
    root_logger.handlers.clear()

    # Add our custom handlers
    root_logger.addHandler(_create_console_handler())
    root_logger.addHandler(_create_file_handler())

    # ── Step 2: Shared processors (run for BOTH outputs) ──
    shared_processors: list[structlog.types.Processor] = [
        # Add log level string: "info", "error", etc
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add ISO timestamp
        structlog.processors.TimeStamper(fmt="ISO"),
        # If there's an exception, format it nicely
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # Unicode decode errors → replace instead of crash
        structlog.processors.UnicodeDecoder(),
    ]

    # ── Step 3: Configure structlog ──
    structlog.configure(
        processors=[
            # Filter by log level
            structlog.stdlib.filter_by_level,
            # Shared processors
            *shared_processors,
            # Prepare for final rendering
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # ── Step 4: Set formatters per handler ──
    # Console → human readable colored output
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
        foreign_pre_chain=shared_processors,
    )

    # File → JSON lines (one JSON object per line)
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    # Apply formatters to handlers
    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.setFormatter(file_formatter)
        elif isinstance(handler, logging.StreamHandler):
            handler.setFormatter(console_formatter)

    return structlog.get_logger()


# ──────────────────────────────────────
# Module-level singleton
# ──────────────────────────────────────
logger = setup_logger()