"""
Tests for POST /orders - Create Order.

Test categories:
- Positive: valid order creation with different params
- Negative: invalid payloads that should fail
- Boundary: edge case amounts

Each test is independent - no test depends on another.
"""

import pytest
import allure
from allure import severity_level as Severity

from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import (
    OrderResponse,
    OrderStatus,
    Currency,
)


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Create Order")
@pytest.mark.orders
class TestCreateOrderPositive:
    """Positive test cases for order creation."""

    @pytest.mark.smoke
    @allure.title("Create order with valid INR amount")
    @allure.severity(Severity.CRITICAL)
    def test_create_order_with_valid_amount(self, orders_api: OrdersAPI):
        """
        Most basic happy path.
        Create order with minimum required fields.

        Verifications:
        1. Order ID is returned and starts with 'order_'
        2. Amount matches what we sent
        3. Status is CREATED
        4. Currency is INR
        5. Amount due equals full amount
        6. Amount paid is zero
        """
        order = orders_api.create_order(amount=50000)

        assert order.id.startswith("order_"), (
            f"Order ID should start with 'order_', got: {order.id}"
        )
        assert order.amount == 50000, (
            f"Amount should be 50000, got: {order.amount}"
        )
        assert order.status == OrderStatus.CREATED, (
            f"Status should be CREATED, got: {order.status}"
        )
        assert order.currency == Currency.INR, (
            f"Currency should be INR, got: {order.currency}"
        )
        assert order.amount_due == 50000, (
            f"Amount due should equal amount, got: {order.amount_due}"
        )
        assert order.amount_paid == 0, (
            f"Amount paid should be 0, got: {order.amount_paid}"
        )

    @allure.title("Create order with receipt")
    @allure.severity(Severity.NORMAL)
    def test_create_order_with_receipt(self, orders_api: OrdersAPI):
        """
        Verify receipt field is stored correctly.
        Receipt is used for merchant's internal tracking.
        """
        receipt = "test_receipt_123"

        order = orders_api.create_order(
            amount=75000,
            receipt=receipt,
        )

        assert order.id.startswith("order_")
        assert order.receipt == receipt, (
            f"Receipt should be '{receipt}', got: {order.receipt}"
        )

    @allure.title("Create order with notes")
    @allure.severity(Severity.NORMAL)
    def test_create_order_with_notes(self, orders_api: OrdersAPI):
        """
        Verify notes (key-value metadata) are stored.
        Razorpay allows up to 15 key-value pairs.
        """
        notes = {
            "customer_name": "John Doe",
            "internal_id": "INT_12345",
        }

        order = orders_api.create_order(
            amount=30000,
            notes=notes,
        )

        assert order.id.startswith("order_")
        assert isinstance(order.notes, dict), (
            f"Notes should be dict, got: {type(order.notes)}"
        )
        assert order.notes["customer_name"] == "John Doe"
        assert order.notes["internal_id"] == "INT_12345"

    @allure.title("Create order with partial payment enabled")
    @allure.severity(Severity.NORMAL)
    def test_create_order_with_partial_payment(self, orders_api: OrdersAPI):
        """
        Verify order is created with partial_payment flag.
        When enabled, customer can pay less than full amount.
        """
        order = orders_api.create_order(
            amount=100000,
            partial_payment=True,
        )

        assert order.id.startswith("order_")
        assert order.amount == 100000

    @allure.title("Create order with all optional fields")
    @allure.severity(Severity.NORMAL)
    def test_create_order_with_all_fields(self, orders_api: OrdersAPI):
        """
        Full payload with every optional field filled.
        Real-world usage typically sends all fields.
        """
        order = orders_api.create_order(
            amount=250000,
            currency=Currency.INR,
            receipt="full_payload_receipt",
            notes={
                "customer": "Jane Doe",
                "order_type": "premium",
                "source": "api_test",
            },
            partial_payment=False,
        )

        assert order.id.startswith("order_")
        assert order.amount == 250000
        assert order.currency == Currency.INR
        assert order.receipt == "full_payload_receipt"
        assert order.status == OrderStatus.CREATED
        assert order.attempts == 0

    @allure.title("Create order returns valid entity type")
    @allure.severity(Severity.MINOR)
    def test_create_order_entity_is_order(self, orders_api: OrdersAPI):
        """Razorpay always returns entity='order' for order responses."""
        order = orders_api.create_order(amount=50000)

        assert order.entity == "order", (
            f"Entity should be 'order', got: {order.entity}"
        )

    @allure.title("Create order returns valid timestamp")
    @allure.severity(Severity.MINOR)
    def test_create_order_has_valid_timestamp(self, orders_api: OrdersAPI):
        """created_at should be a valid unix timestamp."""
        order = orders_api.create_order(amount=50000)

        assert order.created_at > 0, (
            f"created_at should be positive, got: {order.created_at}"
        )
        # Verify it can be converted to datetime without error
        dt = order.created_at_datetime
        assert dt is not None


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Create Order - Boundary")
@pytest.mark.orders
class TestCreateOrderBoundary:
    """Boundary value tests for order creation."""

    @allure.title("Create order with minimum amount (₹1 = 100 paise)")
    @allure.severity(Severity.CRITICAL)
    def test_create_order_minimum_amount(self, orders_api: OrdersAPI):
        """
        Razorpay minimum is ₹1 = 100 paise.
        Verify system accepts the boundary value.
        """
        order = orders_api.create_order(amount=100)

        assert order.amount == 100
        assert order.amount_in_rupees == 1.0

    @allure.title("Create order with large amount")
    @allure.severity(Severity.NORMAL)
    def test_create_order_large_amount(self, orders_api: OrdersAPI):
        """Test with ₹1,00,000 = 1 lakh."""
        order = orders_api.create_order(amount=100_000_00)

        assert order.amount == 100_000_00
        assert order.amount_in_rupees == 100_000.0


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Create Order - Negative")
@pytest.mark.orders
@pytest.mark.negative
class TestCreateOrderNegative:
    """
    Negative tests - verify API rejects bad input correctly.
    
    Uses create_order_raw() because:
    → We WANT to send invalid data
    → Pydantic models would block us before reaching API
    → Raw methods bypass model validation
    """

    @allure.title("Create order with missing amount returns 400")
    @allure.severity(Severity.CRITICAL)
    def test_create_order_missing_amount(self, orders_api: OrdersAPI):
        """Amount is required. Missing it should return 400."""
        response = orders_api.create_order_raw(
            payload={"currency": "INR"}
        )

        assert response.status_code == 400, (
            f"Expected 400, got: {response.status_code}"
        )
        error = response.json().get("error", {})
        assert error.get("code") == "BAD_REQUEST_ERROR"

    @allure.title("Create order with zero amount returns 400")
    @allure.severity(Severity.CRITICAL)
    def test_create_order_zero_amount(self, orders_api: OrdersAPI):
        """Amount = 0 should be rejected."""
        response = orders_api.create_order_raw(
            payload={"amount": 0, "currency": "INR"}
        )

        assert response.status_code == 400

    @allure.title("Create order with negative amount returns 400")
    @allure.severity(Severity.NORMAL)
    def test_create_order_negative_amount(self, orders_api: OrdersAPI):
        """Negative amount should be rejected."""
        response = orders_api.create_order_raw(
            payload={"amount": -50000, "currency": "INR"}
        )

        assert response.status_code == 400

    @allure.title("Create order with invalid currency returns 400")
    @allure.severity(Severity.NORMAL)
    def test_create_order_invalid_currency(self, orders_api: OrdersAPI):
        """Currency must be valid ISO code."""
        response = orders_api.create_order_raw(
            payload={"amount": 50000, "currency": "INVALID"}
        )

        assert response.status_code == 400

    @allure.title("Create order with empty payload returns 400")
    @allure.severity(Severity.NORMAL)
    def test_create_order_empty_payload(self, orders_api: OrdersAPI):
        """Completely empty body should fail."""
        response = orders_api.create_order_raw(payload={})

        assert response.status_code == 400

    @allure.title("Create order with string amount returns 400")
    @allure.severity(Severity.NORMAL)
    def test_create_order_string_amount(self, orders_api: OrdersAPI):
        """Amount must be integer, not string."""
        response = orders_api.create_order_raw(
            payload={"amount": "fifty thousand", "currency": "INR"}
        )

        assert response.status_code == 400

    @allure.title("Create order with amount below minimum returns 400")
    @allure.severity(Severity.NORMAL)
    def test_create_order_below_minimum_amount(self, orders_api: OrdersAPI):
        """Amount below ₹1 (99 paise) should be rejected."""
        response = orders_api.create_order_raw(
            payload={"amount": 99, "currency": "INR"}
        )

        assert response.status_code == 400