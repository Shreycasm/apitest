"""
Orders-specific fixtures.
All fixtures are parallel-safe with unique identifiers.
"""

import pytest
from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import OrderResponse, Currency
from src.razorpay.utils.test_helpers import (
    unique_receipt,
    unique_notes,
)


@pytest.fixture(scope="function")
def shared_order(orders_api: OrdersAPI) -> OrderResponse:
    """
    Changed from module to function scope for parallel safety.
    Each test/worker gets its own order.
    """
    return orders_api.create_order(
        amount=75000,
        currency=Currency.INR,
        receipt=unique_receipt("shared"),
        notes=unique_notes({"scope": "shared", "purpose": "read_tests"}),
    )


@pytest.fixture(scope="function")
def order_id_for_update(orders_api: OrdersAPI) -> str:
    """
    Returns a fresh order ID ready to be updated.
    Unique receipt ensures no collision in parallel.
    """
    order = orders_api.create_order(
        amount=25000,
        currency=Currency.INR,
        receipt=unique_receipt("update"),
        notes=unique_notes({"original": "true"}),
    )
    return order.id