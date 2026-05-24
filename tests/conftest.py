"""
Root conftest.py

Fixtures defined here are available to ALL test files.
No imports needed in test files - pytest injects them automatically.

Fixture dependency chain:
    http_client (session)
        └→ orders_api (session)
        └→ payments_api (session)
        └→ refunds_api (session)
            └→ created_order (function)
                └→ paid_order (module) [future]
"""

import pytest
import shutil
from pathlib import Path

from src.razorpay.api.base_client import RazorpayClient
from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import OrderResponse, Currency
from src.razorpay.config.settings import settings
from src.razorpay.utils.logger import logger
from src.razorpay.utils.validators import SchemaValidator
from src.razorpay.utils.log_context import TestLogContext

# ─── Add these imports at the top ───
from src.razorpay.utils.test_helpers import (
    unique_receipt,
    unique_notes,
    random_amount,
    random_receipt,
    random_customer_notes,
)

# ─────────────────────────────────────────────────
# INFRASTRUCTURE FIXTURES
# Created once per session = fast
# ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def http_client() -> RazorpayClient:
    """
    Single HTTP client for entire test session.
    
    scope="session" → created ONCE, reused across ALL tests.
    Saves time: no repeated TCP handshakes.
    
    yield → everything before yield is SETUP
            everything after yield is TEARDOWN
    """
    log = logger.bind(fixture="http_client")
    log.info("creating_http_client")

    client = RazorpayClient()
    yield client

    # Teardown: runs after ALL tests complete
    log.info("closing_http_client")
    client.close()


@pytest.fixture(scope="session")
def orders_api(http_client: RazorpayClient) -> OrdersAPI:
    """
    OrdersAPI instance for entire test session.
    
    Depends on http_client fixture.
    Pytest resolves dependencies automatically.
    """
    return OrdersAPI(client=http_client)



# ─────────────────────────────────────────────────
# DATA FIXTURES
# Created fresh per test = isolated
# ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def created_order(orders_api: OrdersAPI) -> OrderResponse:
    """
    Creates a fresh order for each test that needs one.

    scope="function" → each test gets its OWN order.
    No test shares state with another.

    Why not session scope?
    → If test A modifies the order, test B sees corrupted state
    → function scope = complete isolation

    Usage in test:
        def test_something(self, created_order):
            print(created_order.id)   # ready to use
    """
    log = logger.bind(fixture="created_order")
    log.info("creating_test_order")

    order = orders_api.create_order(
        amount=50000,
        currency=Currency.INR,
        receipt="pytest_fixture_receipt",
        notes={
            "env": settings.environment,
            "created_by": "pytest_fixture",
        },
    )

    log.info("test_order_created", order_id=order.id)
    return order


@pytest.fixture(scope="function")
def created_order_with_notes(orders_api: OrdersAPI) -> OrderResponse:
    """
    Creates an order with specific notes.
    Use when test specifically needs notes to be set.
    """
    return orders_api.create_order(
        amount=100000,
        currency=Currency.INR,
        receipt="pytest_notes_receipt",
        notes={
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "purpose": "fixture_test",
        },
    )


@pytest.fixture(scope="function")
def minimum_order(orders_api: OrdersAPI) -> OrderResponse:
    """
    Creates order with minimum valid amount (100 paise = ₹1).
    Use for boundary value tests.
    """
    return orders_api.create_order(
        amount=100,
        currency=Currency.INR,
        receipt="pytest_min_receipt",
    )


@pytest.fixture(scope="function")
def large_order(orders_api: OrdersAPI) -> OrderResponse:
    """
    Creates order with large amount.
    Use for large transaction tests.
    """
    return orders_api.create_order(
        amount=10_000_00,   # ₹10,000
        currency=Currency.INR,
        receipt="pytest_large_receipt",
    )


# ─────────────────────────────────────────────────
# CONFIGURATION FIXTURES
# ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def api_settings():
    """
    Expose settings to tests that need them.
    
    Usage:
        def test_something(self, api_settings):
            assert api_settings.environment == "staging"
    """
    return settings


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for direct URL assertions in tests."""
    return settings.razorpay_base_url


# ─────────────────────────────────────────────────
# PYTEST HOOKS
# These run automatically, no need to call them
# ─────────────────────────────────────────────────

def pytest_configure(config: pytest.Config) -> None:
    """
    Runs once when pytest starts.
    Register custom markers here to avoid warnings.
    """
    config.addinivalue_line(
        "markers", "smoke: Quick smoke tests - run first"
    )
    config.addinivalue_line(
        "markers", "regression: Full regression suite"
    )
    config.addinivalue_line(
        "markers", "orders: Order related tests"
    )
    config.addinivalue_line(
        "markers", "payments: Payment related tests"
    )
    config.addinivalue_line(
        "markers", "refunds: Refund related tests"
    )
    config.addinivalue_line(
        "markers", "negative: Negative/error path tests"
    )


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """
    Runs after each test phase (setup/call/teardown).
    Log test result automatically.
    """
    log = logger.bind(hook="pytest_runtest_logreport")

    if report.when == "call":
        if report.passed:
            log.info("test_passed", test=report.nodeid)
        elif report.failed:
            log.error("test_failed", test=report.nodeid)
        elif report.skipped:
            log.warning("test_skipped", test=report.nodeid)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Runs when pytest session begins."""
    log = logger.bind(hook="pytest_sessionstart")
    log.info(
        "test_session_started",
        environment=settings.environment,
        base_url=settings.razorpay_base_url,
    )


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
) -> None:
    """Runs when pytest session ends."""
    log = logger.bind(hook="pytest_sessionfinish")
    log.info(
        "test_session_finished",
        exit_status=exitstatus,
        total_tests=session.testscollected,
    )



@pytest.fixture(scope="session")
def schema_validator() -> SchemaValidator:
    """
    Schema validator instance.
    Shared across all tests (session scope).
    Schemas are cached after first load.
    """
    return SchemaValidator()




def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
) -> None:
    """
    Runs when pytest session ends.
    Copy allure categories and generate environment file.
    """
    log = logger.bind(hook="pytest_sessionfinish")
    log.info(
        "test_session_finished",
        exit_status=exitstatus,
        total_tests=session.testscollected,
    )

    # Copy categories file to allure results
    categories_src = Path("test_data/allure_categories.json")
    categories_dst = Path("allure-results/categories.json")

    if categories_src.exists():
        categories_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(categories_src, categories_dst)
        log.info("allure_categories_copied")

    # Generate environment properties
    try:
        env_file = Path("allure-results/environment.properties")
        env_file.parent.mkdir(parents=True, exist_ok=True)
        with open(env_file, "w") as f:
            f.write(f"Environment={settings.environment}\n")
            f.write(f"Base.URL={settings.razorpay_base_url}\n")
            f.write(f"Framework=razorpay-automation/1.0.0\n")
        log.info("allure_environment_generated")
    except Exception as e:
        log.warning("allure_env_generation_failed", error=str(e))


# ─────────────────────────────────────────────────
# LOGGING FIXTURES
# ─────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def test_logger(request: pytest.FixtureRequest):
    """
    Automatic test lifecycle logger.

    autouse=True → runs for EVERY test without being requested.
    No need to add 'test_logger' to test function args.

    Logs:
    - Test start (with test name)
    - Test end (with status + duration)

    Example log output:
        {"event": "test_started", "test": "test_create_order", "phase": "setup"}
        {"event": "test_finished", "test": "test_create_order", "status": "passed", "duration_ms": 523}
    """
    ctx = TestLogContext(test_name=request.node.nodeid)
    ctx.start()

    yield ctx

    # Determine test result
    # request.node has the test result after execution
    if hasattr(request.node, "rep_call"):
        if request.node.rep_call.passed:
            status = "passed"
        elif request.node.rep_call.failed:
            status = "failed"
        else:
            status = "skipped"
    else:
        status = "unknown"

    ctx.end(status=status)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test result and attach to request.node.

    This makes test result available in fixtures via:
        request.node.rep_setup
        request.node.rep_call
        request.node.rep_teardown
    """
    import pytest
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

# ─────────────────────────────────────────────────
# PARALLEL-SAFE DATA FIXTURES
# ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def parallel_order(orders_api: OrdersAPI) -> OrderResponse:
    """
    Parallel-safe order fixture.
    
    Unlike created_order, this uses unique receipt and notes
    so orders from different workers never collide.
    """
    order = orders_api.create_order(
        amount=random_amount(min_rupees=10, max_rupees=1000),
        currency=Currency.INR,
        receipt=unique_receipt("parallel"),
        notes=unique_notes({"fixture": "parallel_order"}),
    )
    return order


@pytest.fixture(scope="function")
def unique_order_receipt() -> str:
    """Get a unique receipt string for test use."""
    return unique_receipt("test")


@pytest.fixture(scope="function")
def unique_order_notes() -> dict[str, str]:
    """Get unique notes dict for test use."""
    return unique_notes()