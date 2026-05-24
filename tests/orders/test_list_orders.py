"""
Tests for GET /orders - List Orders.

Tests pagination, filtering, and response structure.
"""

import time

import allure
import pytest
from allure import severity_level as Severity

from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import (
    OrderListResponse,
    OrderResponse,
)


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("List Orders")
@pytest.mark.orders
class TestListOrdersPositive:
    """Positive tests for listing orders."""

    @pytest.mark.smoke
    @allure.title("List orders returns collection response")
    @allure.severity(Severity.CRITICAL)
    def test_list_orders_returns_collection(
        self,
        orders_api: OrdersAPI,
    ):
        """
        Default list call should return valid collection.
        Entity should be 'collection', items should be list.
        """

        result = orders_api.list_orders()

        assert result.entity == "collection", (
            f"Entity should be 'collection', got: {result.entity}"
        )

        assert isinstance(result.items, list)

        assert result.count >= len(result.items)

    @allure.title("List orders respects count parameter")
    @allure.severity(Severity.CRITICAL)
    def test_list_orders_with_count(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
    ):
        """
        count=2 should return at most 2 items.
        created_order fixture ensures at least 1 exists.
        """

        result = orders_api.list_orders(count=2)

        assert len(result.items) <= 2, (
            f"Should return max 2, got: {len(result.items)}"
        )

    @allure.title("List orders with skip for pagination")
    @allure.severity(Severity.NORMAL)
    def test_list_orders_with_skip(
        self,
        orders_api: OrdersAPI,
    ):
        """
        Skip should offset results.
        Used for pagination in real apps.
        """

        result = orders_api.list_orders(
            count=5,
            skip=0,
        )

        assert isinstance(result, OrderListResponse)

        assert result.count >= len(result.items)

    @allure.title("List orders items are valid OrderResponse objects")
    @allure.severity(Severity.NORMAL)
    def test_list_orders_items_are_valid(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
    ):
        """Each item in list should be fully valid order."""

        result = orders_api.list_orders(count=3)

        for order in result.items:

            assert order.id.startswith("order_")

            assert order.amount > 0

            assert order.entity == "order"

            assert order.created_at > 0

    @allure.title("List orders order_ids helper returns correct IDs")
    @allure.severity(Severity.MINOR)
    def test_list_orders_ids_helper(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
    ):
        """Verify the order_ids computed property works."""

        result = orders_api.list_orders(count=5)

        ids = result.order_ids

        assert isinstance(ids, list)

        for oid in ids:
            assert oid.startswith("order_")

    @pytest.mark.flaky(reruns=2, reruns_delay=2)
    @allure.title("Newly created order appears in list")
    @allure.severity(Severity.CRITICAL)
    def test_created_order_appears_in_list(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
    ):
        """
        After creating an order, it should show up in listing.

        Razorpay list APIs are eventually consistent,
        so we retry a few times before failing.
        """

        found = False

        for _ in range(5):

            result = orders_api.list_orders(count=20)

            if created_order.id in result.order_ids:
                found = True
                break

            time.sleep(1)

        assert found, (
            f"Created order {created_order.id} not found in list "
            f"after retries."
        )


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("List Orders - Negative")
@pytest.mark.orders
@pytest.mark.negative
class TestListOrdersNegative:
    """Negative tests for listing orders."""

    @allure.title("List orders with count > 100 raises ValueError")
    @allure.severity(Severity.NORMAL)
    def test_list_orders_count_exceeds_max(
        self,
        orders_api: OrdersAPI,
    ):
        """
        Our API layer validates count <= 100.
        Should raise ValueError before API call.
        """

        with pytest.raises(
            ValueError,
            match="count cannot exceed 100",
        ):
            orders_api.list_orders(count=101)

    @allure.title("List orders with negative skip raises ValueError")
    @allure.severity(Severity.NORMAL)
    def test_list_orders_negative_skip(
        self,
        orders_api: OrdersAPI,
    ):
        """
        Negative skip makes no sense.
        Our validation should catch it.
        """

        with pytest.raises(
            ValueError,
            match="skip cannot be negative",
        ):
            orders_api.list_orders(skip=-1)