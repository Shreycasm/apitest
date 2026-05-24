"""
Log context manager.

Adds contextual information to ALL log lines
within a block. No need to pass data to every log call.

Usage:
    with LogContext(test_name="test_create_order", order_id="order_xxx"):
        logger.info("step_1")   # automatically has test_name and order_id
        logger.info("step_2")   # automatically has test_name and order_id
"""

from contextlib import contextmanager
from typing import Any

import structlog

from src.razorpay.utils.logger import logger


@contextmanager
def log_context(**kwargs: Any):
    """
    Context manager that binds key-value pairs to all logs inside the block.

    Args:
        **kwargs: Key-value pairs to add to every log line

    Example:
        with log_context(test="test_create_order", env="staging"):
            logger.info("starting")
            # Output: {"test": "test_create_order", "env": "staging", "event": "starting"}
            
            do_something()
            logger.info("finished")
            # Output: {"test": "test_create_order", "env": "staging", "event": "finished"}
    """
    bound_logger = logger.bind(**kwargs)

    # Temporarily replace the module-level logger
    token = structlog.contextvars.bind_contextvars(**kwargs)

    try:
        yield bound_logger
    finally:
        # Remove the context after block exits
        structlog.contextvars.unbind_contextvars(*kwargs.keys())


class TestLogContext:
    """
    Class-based log context for test lifecycle.

    Tracks test phases: setup → execution → teardown
    with timing information.

    Usage in conftest:
        @pytest.fixture(autouse=True)
        def test_logger(request):
            ctx = TestLogContext(request.node.nodeid)
            ctx.start()
            yield ctx
            ctx.end()
    """

    def __init__(self, test_name: str) -> None:
        self.test_name = test_name
        self._log = logger.bind(test=test_name)
        self._start_time: float = 0

    def start(self) -> None:
        """Log test start."""
        import time
        self._start_time = time.perf_counter()
        self._log.info(
            "test_started",
            phase="setup",
        )

    def step(self, step_name: str, **kwargs: Any) -> None:
        """Log a test step with optional data."""
        self._log.info(
            "test_step",
            step=step_name,
            **kwargs,
        )

    def end(self, status: str = "unknown") -> None:
        """Log test end with duration."""
        import time
        duration_ms = round(
            (time.perf_counter() - self._start_time) * 1000, 2
        )
        self._log.info(
            "test_finished",
            phase="teardown",
            status=status,
            duration_ms=duration_ms,
        )