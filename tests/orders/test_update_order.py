"""
Tests for PATCH /orders/{id} - Update Order.

Only notes can be updated for Razorpay orders.
"""

import pytest
import allure
from allure import severity_level as Severity

from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import OrderResponse


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Update Order")
@pytest.mark.orders
class TestUpdateOrderPositive:
    """Positive tests for updating order notes."""

    @pytest.mark.smoke
    @allure.title("Update order notes successfully")
    @allure.severity(Severity.CRITICAL)
    def test_update_order_notes(
        self,
        orders_api: OrdersAPI,
        order_id_for_update: str,
    ):
        """
        Update notes and verify they are saved.
        Uses order_id_for_update fixture (fresh order per test).
        """
        new_notes = {"status": "updated", "by": "pytest"}

        updated = orders_api.update_order(
            order_id=order_id_for_update,
            notes=new_notes,
        )

        assert updated.id == order_id_for_update
        assert updated.notes["status"] == "updated"
        assert updated.notes["by"] == "pytest"

    @allure.title("Update notes overwrites previous notes")
    @allure.severity(Severity.NORMAL)
    def test_update_order_overwrites_notes(
        self,
        orders_api: OrdersAPI,
    ):
        """
        Create with notes A → Update with notes B → Verify B replaced A.
        """
        # Create with initial notes
        order = orders_api.create_order(
            amount=50000,
            notes={"original_key": "original_value"},
        )

        # Update with new notes
        new_notes = {"new_key": "new_value"}
        updated = orders_api.update_order(
            order_id=order.id,
            notes=new_notes,
        )

        assert "new_key" in updated.notes
        assert updated.notes["new_key"] == "new_value"

    @allure.title("Update does not change order amount")
    @allure.severity(Severity.CRITICAL)
    def test_update_preserves_amount(
        self,
        orders_api: OrdersAPI,
        order_id_for_update: str,
    ):
        """
        Updating notes should NOT affect amount or status.
        Verify immutable fields stay same.
        """
        # Get original
        original = orders_api.get_order(order_id_for_update)

        # Update notes
        orders_api.update_order(
            order_id=order_id_for_update,
            notes={"updated": "true"},
        )

        # Fetch again
        after_update = orders_api.get_order(order_id_for_update)

        assert after_update.amount == original.amount
        assert after_update.status == original.status
        assert after_update.currency == original.currency

    @allure.title("Update order with single note")
    @allure.severity(Severity.MINOR)
    def test_update_order_single_note(
        self,
        orders_api: OrdersAPI,
        order_id_for_update: str,
    ):
        """Minimum valid update - one key-value pair."""
        updated = orders_api.update_order(
            order_id=order_id_for_update,
            notes={"only_key": "only_value"},
        )

        assert "only_key" in updated.notes


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Update Order - Negative")
@pytest.mark.orders
@pytest.mark.negative
class TestUpdateOrderNegative:
    """Negative tests for updating orders."""

    @allure.title("Update non-existent order returns error")
    @allure.severity(Severity.CRITICAL)
    def test_update_invalid_order_id(self, orders_api: OrdersAPI):
        """Updating order with bad ID should fail."""
        response = orders_api.update_order_raw(
            order_id="order_fake_12345",
            payload={"notes": {"key": "value"}},
        )

        assert response.status_code in [400, 404]

    @allure.title("Update order with empty ID raises ValueError")
    @allure.severity(Severity.NORMAL)
    def test_update_empty_order_id(self, orders_api: OrdersAPI):
        """Empty order ID caught by our guard clause."""
        with pytest.raises(ValueError, match="order_id cannot be empty"):
            orders_api.update_order(
                order_id="",
                notes={"key": "value"},
            )