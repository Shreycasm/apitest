"""
Tests for Order API response schema validation.

These tests verify the STRUCTURE of responses,
not the values. Structural bugs are caught here:
- Missing fields
- Wrong types
- Invalid formats
- Unexpected fields

Separate from value tests because:
→ Schema tests = "does the response SHAPE match?"
→ Value tests  = "does the response DATA match?"
Both are needed. Different concerns.
"""

import pytest
import allure
from allure import severity_level as Severity

from src.razorpay.api.orders import OrdersAPI
from src.razorpay.models.order_model import OrderResponse
from src.razorpay.utils.validators import (
    SchemaValidator,
    SchemaValidationError,
)


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Schema Validation")
@pytest.mark.orders
@pytest.mark.regression
class TestOrderSchemaValidation:
    """Validate order response structure matches expected schema."""

    @pytest.mark.smoke
    @allure.title("Create order response matches order schema")
    @allure.severity(Severity.CRITICAL)
    def test_create_order_schema(
        self,
        orders_api: OrdersAPI,
        schema_validator: SchemaValidator,
    ):
        """
        Create order → validate full response against schema.
        This catches structural changes in Razorpay API.
        """
        response = orders_api.create_order_raw(
            payload={
                "amount": 50000,
                "currency": "INR",
                "receipt": "schema_test_001",
            }
        )

        assert response.status_code == 200

        # Schema validation - validates EVERYTHING in one call
        schema_validator.validate_order(response.json())

    @allure.title("Get order response matches order schema")
    @allure.severity(Severity.CRITICAL)
    def test_get_order_schema(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
        schema_validator: SchemaValidator,
    ):
        """Fetch order → validate response schema."""
        response = orders_api.get_order_raw(created_order.id)

        assert response.status_code == 200
        schema_validator.validate_order(response.json())

    @allure.title("List orders response matches collection schema")
    @allure.severity(Severity.CRITICAL)
    def test_list_orders_schema(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
        schema_validator: SchemaValidator,
    ):
        """List orders → validate collection response schema."""
        response = orders_api.list_orders_raw(
            params={"count": 3}
        )

        assert response.status_code == 200
        schema_validator.validate_order_list(response.json())

    @allure.title("Update order response matches order schema")
    @allure.severity(Severity.CRITICAL)
    def test_update_order_schema(
        self,
        orders_api: OrdersAPI,
        created_order: OrderResponse,
        schema_validator: SchemaValidator,
    ):
        """Update order → validate response still matches schema."""
        response = orders_api.update_order_raw(
            order_id=created_order.id,
            payload={"notes": {"schema_test": "true"}},
        )

        assert response.status_code == 200
        schema_validator.validate_order(response.json())

    @allure.title("Order with notes matches schema")
    @allure.severity(Severity.NORMAL)
    def test_order_with_notes_schema(
        self,
        orders_api: OrdersAPI,
        schema_validator: SchemaValidator,
    ):
        """
        Notes can be dict (with data) or empty array.
        Schema handles both via oneOf.
        """
        response = orders_api.create_order_raw(
            payload={
                "amount": 50000,
                "currency": "INR",
                "notes": {
                    "key1": "value1",
                    "key2": "value2",
                },
            }
        )

        assert response.status_code == 200
        schema_validator.validate_order(response.json())

    @allure.title("Order without notes matches schema")
    @allure.severity(Severity.NORMAL)
    def test_order_without_notes_schema(
        self,
        orders_api: OrdersAPI,
        schema_validator: SchemaValidator,
    ):
        """Order created without notes → notes comes back as empty array."""
        response = orders_api.create_order_raw(
            payload={
                "amount": 50000,
                "currency": "INR",
            }
        )

        assert response.status_code == 200
        schema_validator.validate_order(response.json())


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Error Schema Validation")
@pytest.mark.orders
@pytest.mark.negative
@pytest.mark.regression
class TestOrderErrorSchemaValidation:
    """Validate that error responses also have correct structure."""

    @allure.title("Error response matches error schema")
    @allure.severity(Severity.CRITICAL)
    def test_error_response_schema(
        self,
        orders_api: OrdersAPI,
        schema_validator: SchemaValidator,
    ):
        """
        Send bad request → verify error response structure.
        Even errors should be well-structured.
        """
        response = orders_api.create_order_raw(
            payload={"amount": -1, "currency": "INR"}
        )

        assert response.status_code == 400
        schema_validator.validate_error(response.json())

    @allure.title("Missing amount error matches error schema")
    @allure.severity(Severity.NORMAL)
    def test_missing_amount_error_schema(
        self,
        orders_api: OrdersAPI,
        schema_validator: SchemaValidator,
    ):
        """Missing required field → error should still be structured."""
        response = orders_api.create_order_raw(payload={})

        assert response.status_code == 400
        schema_validator.validate_error(response.json())

    @allure.title("Invalid currency error matches error schema")
    @allure.severity(Severity.NORMAL)
    def test_invalid_currency_error_schema(
        self,
        orders_api: OrdersAPI,
        schema_validator: SchemaValidator,
    ):
        """Invalid currency → error should be well-structured."""
        response = orders_api.create_order_raw(
            payload={"amount": 50000, "currency": "FAKE"}
        )

        assert response.status_code == 400
        schema_validator.validate_error(response.json())


@allure.epic("Razorpay API")
@allure.feature("Orders")
@allure.story("Schema Validator Unit Tests")
@pytest.mark.regression
class TestSchemaValidatorItself:
    """
    Test that our validator catches bad data.
    These are unit tests for the validator tool itself.
    """

    @allure.title("Validator catches missing required field")
    @allure.severity(Severity.CRITICAL)
    def test_validator_catches_missing_field(
        self,
        schema_validator: SchemaValidator,
    ):
        """Remove 'id' from response → validator should catch it."""
        bad_response = {
            # "id" is missing!
            "entity": "order",
            "amount": 50000,
            "amount_paid": 0,
            "amount_due": 50000,
            "currency": "INR",
            "status": "created",
            "attempts": 0,
            "created_at": 1700000000,
        }

        with pytest.raises(SchemaValidationError):
            schema_validator.validate_order(bad_response)

    @allure.title("Validator catches wrong type")
    @allure.severity(Severity.CRITICAL)
    def test_validator_catches_wrong_type(
        self,
        schema_validator: SchemaValidator,
    ):
        """amount as string instead of int → should fail."""
        bad_response = {
            "id": "order_abc123",
            "entity": "order",
            "amount": "fifty thousand",   # WRONG TYPE
            "amount_paid": 0,
            "amount_due": 50000,
            "currency": "INR",
            "status": "created",
            "attempts": 0,
            "created_at": 1700000000,
        }

        with pytest.raises(SchemaValidationError):
            schema_validator.validate_order(bad_response)

    @allure.title("Validator catches invalid status enum")
    @allure.severity(Severity.NORMAL)
    def test_validator_catches_invalid_enum(
        self,
        schema_validator: SchemaValidator,
    ):
        """Status must be one of [created, attempted, paid]."""
        bad_response = {
            "id": "order_abc123",
            "entity": "order",
            "amount": 50000,
            "amount_paid": 0,
            "amount_due": 50000,
            "currency": "INR",
            "status": "invalid_status",   # INVALID ENUM
            "attempts": 0,
            "created_at": 1700000000,
        }

        with pytest.raises(SchemaValidationError):
            schema_validator.validate_order(bad_response)

    @allure.title("Validator catches invalid ID format")
    @allure.severity(Severity.NORMAL)
    def test_validator_catches_invalid_id_format(
        self,
        schema_validator: SchemaValidator,
    ):
        """ID must match pattern ^order_[A-Za-z0-9]+$"""
        bad_response = {
            "id": "bad-id-format!!!",   # INVALID PATTERN
            "entity": "order",
            "amount": 50000,
            "amount_paid": 0,
            "amount_due": 50000,
            "currency": "INR",
            "status": "created",
            "attempts": 0,
            "created_at": 1700000000,
        }

        with pytest.raises(SchemaValidationError):
            schema_validator.validate_order(bad_response)

    @allure.title("Validator passes valid complete response")
    @allure.severity(Severity.CRITICAL)
    def test_validator_passes_valid_response(
        self,
        schema_validator: SchemaValidator,
    ):
        """Valid response should pass without error."""
        valid_response = {
            "id": "order_abc123",
            "entity": "order",
            "amount": 50000,
            "amount_paid": 0,
            "amount_due": 50000,
            "currency": "INR",
            "receipt": "receipt_001",
            "status": "created",
            "attempts": 0,
            "notes": [],
            "created_at": 1700000000,
        }

        # Should NOT raise any exception
        schema_validator.validate_order(valid_response)