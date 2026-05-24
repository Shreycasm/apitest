"""
Temporary file to verify fixtures work correctly.
Delete after verification.
"""

import pytest
from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import OrderResponse


class TestFixtureVerification:
    """Verify all fixtures inject correctly."""

    def test_orders_api_fixture(self, orders_api: OrdersAPI):
        """orders_api fixture should be an OrdersAPI instance."""
        assert isinstance(orders_api, OrdersAPI)
        print(f"\n  orders_api type: {type(orders_api)}")

    def test_created_order_fixture(self, created_order: OrderResponse):
        """created_order fixture should return a valid order."""
        assert created_order.id.startswith("order_")
        assert created_order.amount == 50000
        assert created_order.is_created is True
        print(f"\n  Order ID: {created_order.id}")

    def test_each_test_gets_fresh_order(
        self,
        created_order: OrderResponse,
        orders_api: OrdersAPI,
    ):
        """
        Prove function scope works.
        Each test gets its own order.
        """
        another_order = orders_api.create_order(amount=50000)
        assert created_order.id != another_order.id
        print(f"\n  Order 1: {created_order.id}")
        print(f"  Order 2: {another_order.id}")
        print(f"  Different IDs: {created_order.id != another_order.id}")

    def test_minimum_order_fixture(self, minimum_order: OrderResponse):
        """minimum_order fixture gives ₹1 order."""
        assert minimum_order.amount == 100
        print(f"\n  Min Order: {minimum_order.id} = ₹{minimum_order.amount_in_rupees}")

    def test_api_settings_fixture(self, api_settings):
        """Settings fixture works."""
        assert api_settings.environment in ["staging", "production", "dev"]
        print(f"\n  Environment: {api_settings.environment}")