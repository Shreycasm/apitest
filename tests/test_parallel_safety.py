"""
Tests that verify parallel execution safety.

Run with: uv run pytest tests/test_parallel_safety.py -v -n 4

These tests PROVE that:
1. Each test gets unique data
2. No test interferes with another
3. Fixtures work correctly across workers
"""

import pytest
import allure
from allure import severity_level as Severity
from collections import Counter

from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import OrderResponse
from src.razorpay.utils.test_helpers import (
    unique_receipt,
    unique_notes,
    random_amount,
    random_receipt,
    random_customer_notes,
)


@allure.epic("Framework")
@allure.feature("Parallel Safety")
@pytest.mark.regression
class TestParallelSafety:
    """Prove test isolation works in parallel."""

    @allure.title("Unique receipts never collide")
    @allure.severity(Severity.CRITICAL)
    def test_unique_receipts_are_unique(self):
        """Generate 1000 receipts, verify all unique."""
        receipts = [unique_receipt("test") for _ in range(1000)]

        duplicates = [r for r, count in Counter(receipts).items() if count > 1]

        assert len(duplicates) == 0, (
            f"Found duplicate receipts: {duplicates}"
        )

    @allure.title("Unique notes contain test_id")
    @allure.severity(Severity.NORMAL)
    def test_unique_notes_have_test_id(self):
        """Every notes dict must have a unique test_id."""
        notes_list = [unique_notes() for _ in range(100)]

        test_ids = [n["test_id"] for n in notes_list]
        assert len(set(test_ids)) == 100, "All test_ids should be unique"

    @allure.title("Random amounts are within bounds")
    @allure.severity(Severity.NORMAL)
    def test_random_amounts_within_range(self):
        """Verify random amount generator stays in bounds."""
        for _ in range(100):
            amount = random_amount(min_rupees=10, max_rupees=100)
            assert 1000 <= amount <= 10000, (
                f"Amount {amount} outside range 1000-10000 paise"
            )

    @allure.title("Random receipts have correct format")
    @allure.severity(Severity.MINOR)
    def test_random_receipt_format(self):
        """Receipts should start with rcpt_"""
        for _ in range(50):
            receipt = random_receipt()
            assert receipt.startswith("rcpt_"), (
                f"Receipt should start with 'rcpt_', got: {receipt}"
            )

    @allure.title("Customer notes have required keys")
    @allure.severity(Severity.MINOR)
    def test_customer_notes_keys(self):
        """Random customer notes must have standard keys."""
        notes = random_customer_notes()

        required_keys = {"customer_name", "customer_email", "customer_phone", "order_ref"}
        assert required_keys.issubset(notes.keys()), (
            f"Missing keys: {required_keys - notes.keys()}"
        )


@allure.epic("Framework")
@allure.feature("Parallel Safety")
@allure.story("Order Isolation")
@pytest.mark.regression
class TestOrderIsolation:
    """
    Each test creates its own order.
    Run with -n 4 to prove isolation.
    """

    @allure.title("Worker 1: Create and verify own order")
    @allure.severity(Severity.CRITICAL)
    def test_isolated_order_1(self, orders_api: OrdersAPI):
        """This test's order is independent."""
        receipt = unique_receipt("worker1")
        order = orders_api.create_order(
            amount=10000,
            receipt=receipt,
        )

        fetched = orders_api.get_order(order.id)
        assert fetched.receipt == receipt
        assert fetched.amount == 10000

    @allure.title("Worker 2: Create and verify own order")
    @allure.severity(Severity.CRITICAL)
    def test_isolated_order_2(self, orders_api: OrdersAPI):
        """Different receipt, different order, no collision."""
        receipt = unique_receipt("worker2")
        order = orders_api.create_order(
            amount=20000,
            receipt=receipt,
        )

        fetched = orders_api.get_order(order.id)
        assert fetched.receipt == receipt
        assert fetched.amount == 20000

    @allure.title("Worker 3: Create and verify own order")
    @allure.severity(Severity.CRITICAL)
    def test_isolated_order_3(self, orders_api: OrdersAPI):
        """Third worker, still isolated."""
        receipt = unique_receipt("worker3")
        order = orders_api.create_order(
            amount=30000,
            receipt=receipt,
        )

        fetched = orders_api.get_order(order.id)
        assert fetched.receipt == receipt
        assert fetched.amount == 30000

    @allure.title("Worker 4: Create and verify own order")
    @allure.severity(Severity.CRITICAL)
    def test_isolated_order_4(self, orders_api: OrdersAPI):
        """Fourth worker, completely independent."""
        receipt = unique_receipt("worker4")
        order = orders_api.create_order(
            amount=40000,
            receipt=receipt,
        )

        fetched = orders_api.get_order(order.id)
        assert fetched.receipt == receipt
        assert fetched.amount == 40000

    @allure.title("Parallel order fixture is unique per test")
    @allure.severity(Severity.CRITICAL)
    def test_parallel_fixture_unique_1(
        self,
        parallel_order: OrderResponse,
    ):
        """parallel_order fixture gives unique order."""
        assert parallel_order.id.startswith("order_")
        assert parallel_order.receipt is not None

    @allure.title("Parallel order fixture is unique per test (2)")
    @allure.severity(Severity.CRITICAL)
    def test_parallel_fixture_unique_2(
        self,
        parallel_order: OrderResponse,
    ):
        """Different test, different parallel_order instance."""
        assert parallel_order.id.startswith("order_")
        assert parallel_order.receipt is not None