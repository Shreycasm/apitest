"""
Schema validation utilities.

Loads JSON Schema files and validates API responses against them.
Used in tests to verify response STRUCTURE (not just values).
"""

import json
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import validate, ValidationError, RefResolver

from src.razorpay.utils.logger import logger


# ─────────────────────────────────────────
# Schema directory path
# ─────────────────────────────────────────
SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / "test_data" / "schemas"


class SchemaValidator:
    """
    Validates API responses against JSON Schema files.

    Usage:
        validator = SchemaValidator()
        validator.validate_order(response.json())
        validator.validate_order_list(response.json())
        validator.validate_error(response.json())
    """

    def __init__(self) -> None:
        self._log = logger.bind(component="SchemaValidator")
        self._schema_cache: dict[str, dict] = {}

    def _load_schema(self, schema_name: str) -> dict:
        """
        Load and cache a JSON schema file.

        Caching: schema is read from disk ONCE,
        then served from memory on subsequent calls.

        Args:
            schema_name: filename e.g. "order_schema.json"

        Returns:
            Parsed JSON schema as dict
        """
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]

        schema_path = SCHEMA_DIR / schema_name

        if not schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {schema_path}"
            )

        with open(schema_path, "r") as f:
            schema = json.load(f)

        self._schema_cache[schema_name] = schema
        self._log.debug("schema_loaded", schema=schema_name)

        return schema

    def _get_resolver(self) -> RefResolver:
        """
        Create a RefResolver for $ref resolution.

        When order_list_schema.json references order_schema.json
        via $ref, the resolver knows WHERE to find it.
        """
        schema_uri = SCHEMA_DIR.as_uri() + "/"
        return RefResolver(schema_uri, referrer={})

    def validate_response(
        self,
        response_data: dict[str, Any],
        schema_name: str,
    ) -> None:
        """
        Validate any response against a named schema.

        Args:
            response_data: API response as dict
            schema_name: Schema filename

        Raises:
            SchemaValidationError: with clear message on failure
        """
        schema = self._load_schema(schema_name)
        resolver = self._get_resolver()

        try:
            validate(
                instance=response_data,
                schema=schema,
                resolver=resolver,
            )
            self._log.info(
                "schema_validation_passed",
                schema=schema_name,
            )
        except ValidationError as e:
            self._log.error(
                "schema_validation_failed",
                schema=schema_name,
                field=e.json_path,
                message=e.message,
            )
            raise SchemaValidationError(
                schema_name=schema_name,
                field=e.json_path,
                message=e.message,
                response_data=response_data,
            ) from e

    # ─────────────────────────────────────
    # Convenience methods (type-safe)
    # ─────────────────────────────────────
    def validate_order(self, response_data: dict) -> None:
        """Validate single order response."""
        self.validate_response(response_data, "order_schema.json")

    def validate_order_list(self, response_data: dict) -> None:
        """Validate order list/collection response."""
        self.validate_response(response_data, "order_list_schema.json")

    def validate_error(self, response_data: dict) -> None:
        """Validate error response structure."""
        self.validate_response(response_data, "error_schema.json")


class SchemaValidationError(Exception):
    """
    Custom exception for schema validation failures.

    Provides clear, readable error messages instead of
    raw jsonschema exceptions.
    """

    def __init__(
        self,
        schema_name: str,
        field: str,
        message: str,
        response_data: dict,
    ) -> None:
        self.schema_name = schema_name
        self.field = field
        self.message = message
        self.response_data = response_data
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        return (
            f"\n{'=' * 50}\n"
            f"SCHEMA VALIDATION FAILED\n"
            f"{'=' * 50}\n"
            f"Schema : {self.schema_name}\n"
            f"Field  : {self.field}\n"
            f"Error  : {self.message}\n"
            f"{'=' * 50}"
        )