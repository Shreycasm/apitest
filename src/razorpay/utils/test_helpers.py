"""
Test helper utilities.

Provides:
- Unique ID generation (parallel-safe)
- Wait/retry utilities
- Test data generators using Faker
"""

import uuid
import time
from typing import Any, Callable

from faker import Faker

from src.razorpay.utils.logger import logger

fake = Faker()


# ──────────────────────────────────────
# Unique ID Generation
# ──────────────────────────────────────

def unique_receipt(prefix: str = "test") -> str:
    """
    Generate unique receipt for each test.
    
    Why? In parallel execution, two tests might run
    at the same time. If both use "receipt_001",
    we can't tell them apart in logs.

    uuid4 = universally unique, no collision possible.

    Args:
        prefix: Human readable prefix

    Returns:
        e.g. "test_a1b2c3d4"
    """
    short_id = uuid.uuid4().hex[:8]
    return f"{prefix}_{short_id}"


def unique_notes(extra: dict[str, str] | None = None) -> dict[str, str]:
    """
    Generate unique notes with test metadata.

    Always includes a unique test_id so we can trace
    which test created which order, even in parallel.

    Args:
        extra: Additional key-value pairs to include

    Returns:
        Notes dict with unique test_id
    """
    notes = {
        "test_id": uuid.uuid4().hex[:12],
        "created_by": "pytest_parallel",
        "timestamp": str(int(time.time())),
    }
    if extra:
        notes.update(extra)
    return notes


# ──────────────────────────────────────
# Fake Data Generators
# ──────────────────────────────────────

def random_amount(
    min_rupees: int = 1,
    max_rupees: int = 10000,
) -> int:
    """
    Generate random amount in paise.

    Args:
        min_rupees: Minimum amount in rupees
        max_rupees: Maximum amount in rupees

    Returns:
        Amount in paise (rupees × 100)
    """
    rupees = fake.random_int(min=min_rupees, max=max_rupees)
    return rupees * 100


def random_receipt() -> str:
    """Generate receipt with realistic format."""
    return f"rcpt_{fake.bothify('??##??##')}"


def random_customer_notes() -> dict[str, str]:
    """Generate realistic customer notes."""
    return {
        "customer_name": fake.name(),
        "customer_email": fake.email(),
        "customer_phone": fake.phone_number()[:10],
        "order_ref": fake.bothify("ORD-####-??"),
    }


# ──────────────────────────────────────
# Retry Utility
# ──────────────────────────────────────

def retry_on_failure(
    func: Callable,
    max_retries: int = 3,
    delay_seconds: float = 1.0,
    expected_exception: type[Exception] = Exception,
) -> Any:
    """
    Retry a function call on failure.

    Useful for eventually-consistent API behaviors.
    e.g. Order created but takes 1s to appear in list.

    Args:
        func: Callable to retry
        max_retries: How many times to try
        delay_seconds: Wait between retries
        expected_exception: Which exception triggers retry

    Returns:
        Function result on success

    Raises:
        Last exception if all retries fail
    """
    log = logger.bind(component="retry")
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            result = func()
            if attempt > 1:
                log.info(
                    "retry_succeeded",
                    attempt=attempt,
                    max_retries=max_retries,
                )
            return result

        except expected_exception as e:
            last_exception = e
            log.warning(
                "retry_attempt_failed",
                attempt=attempt,
                max_retries=max_retries,
                error=str(e),
            )
            if attempt < max_retries:
                time.sleep(delay_seconds)

    raise last_exception  # type: ignore