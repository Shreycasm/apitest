"""
Tests for GET /orders/{id} - Fetch Single Order.

Tests that fetching an order returns correct and complete data.
"""

import pytest
import allure
from allure import severity_level as Severity

from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import (
    OrderResponse,
    OrderStatus,
)


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Get Order")
@pytest.mark.orders
class TestGetOrderPositive:
    """Positive tests for fetching order by ID."""

    @pytest.mark.smoke
    @allure.title("Fetch order by valid ID returns correct order")
    @allure.severity(Severity.CRITICAL)
    def test_get_order_returns_correct_id(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
    ):
        """
        Create order → Fetch by ID → Verify same order returned.
        
        Uses created_order fixture (function scope).
        Fresh order guaranteed for this test.
        """
        fetched = orders_api.get_order(created_order.id)

        assert fetched.id == created_order.id, (
            f"Expected ID {created_order.id}, got {fetched.id}"
        )

    @allure.title("Fetched order has all required fields")
    @allure.severity(Severity.CRITICAL)
    def test_get_order_has_all_fields(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
    ):
        """Every field from create should exist in fetch."""
        fetched = orders_api.get_order(created_order.id)

        assert fetched.id is not None
        assert fetched.entity == "order"
        assert fetched.amount == created_order.amount
        assert fetched.amount_paid == 0
        assert fetched.amount_due == created_order.amount
        assert fetched.currency == created_order.currency
        assert fetched.status == OrderStatus.CREATED
        assert fetched.attempts == 0
        assert fetched.created_at > 0

    @allure.title("Fetched order amount matches created amount")
    @allure.severity(Severity.CRITICAL)
    def test_get_order_amount_matches(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
    ):
        """Amount should not change between create and fetch."""
        fetched = orders_api.get_order(created_order.id)

        assert fetched.amount == created_order.amount
        assert fetched.amount_due == created_order.amount_due
        assert fetched.amount_paid == created_order.amount_paid

    @allure.title("Fetched order preserves receipt")
    @allure.severity(Severity.NORMAL)
    def test_get_order_preserves_receipt(self, orders_api: OrdersAPI):
        """Receipt set during creation should be returned on fetch."""
        receipt = "get_test_receipt_456"
        order = orders_api.create_order(
            amount=50000,
            receipt=receipt,
        )

        fetched = orders_api.get_order(order.id)

        assert fetched.receipt == receipt

    @allure.title("Fetched order preserves notes")
    @allure.severity(Severity.NORMAL)
    def test_get_order_preserves_notes(self, orders_api: OrdersAPI):
        """Notes set during creation should be returned on fetch."""
        notes = {"key1": "value1", "key2": "value2"}
        order = orders_api.create_order(
            amount=50000,
            notes=notes,
        )

        fetched = orders_api.get_order(order.id)

        assert fetched.notes == notes


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Get Order - Negative")
@pytest.mark.orders
@pytest.mark.negative
class TestGetOrderNegative:
    """Negative tests for fetching order."""

    @allure.title("Fetch non-existent order returns 400")
    @allure.severity(Severity.CRITICAL)
    def test_get_order_invalid_id(self, orders_api: OrdersAPI):
        """Completely invalid order ID should return error."""
        response = orders_api.get_order_raw("order_invalid_123456")

        assert response.status_code == 400

    @allure.title("Fetch order with random string ID returns error")
    @allure.severity(Severity.NORMAL)
    def test_get_order_random_string(self, orders_api: OrdersAPI):
        """Random string that is not an order ID format."""
        response = orders_api.get_order_raw("not_an_order_id")

        assert response.status_code in [400, 404]

    @allure.title("Fetch order with empty ID raises ValueError")
    @allure.severity(Severity.NORMAL)
    def test_get_order_empty_id(self, orders_api: OrdersAPI):
        """
        Empty ID should be caught by OUR code
        before reaching the API.
        We added guard clause in orders.py.
        """
        with pytest.raises(ValueError, match="order_id cannot be empty"):
            orders_api.get_order("")