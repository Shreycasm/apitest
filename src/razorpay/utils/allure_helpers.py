"""
Allure reporting helpers.

Attach request/response data to allure reports automatically.
When a test fails, you see EXACTLY what was sent and received.
"""

import json
from typing import Any

import allure
from requests import Response

from src.razorpay.utils.logger import logger


def attach_request(
    method: str,
    url: str,
    headers: dict | None = None,
    body: dict | None = None,
    params: dict | None = None,
) -> None:
    """
    Attach HTTP request details to allure report.

    Shows up as a collapsible section in the test report.
    Helps debugging: see exactly what was sent.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL
        headers: Request headers (auth redacted)
        body: Request body
        params: Query parameters
    """
    request_data = {
        "method": method,
        "url": url,
    }

    if params:
        request_data["params"] = params
    if body:
        request_data["body"] = body
    if headers:
        # Redact auth header for security
        safe_headers = {
            k: "***REDACTED***" if k.lower() == "authorization" else v
            for k, v in headers.items()
        }
        request_data["headers"] = safe_headers

    allure.attach(
        json.dumps(request_data, indent=2),
        name="HTTP Request",
        attachment_type=allure.attachment_type.JSON,
    )


def attach_response(response: Response) -> None:
    """
    Attach HTTP response details to allure report.

    Shows status code, headers, body, and timing.
    Critical for debugging failed tests.

    Args:
        response: requests.Response object
    """
    response_data = {
        "status_code": response.status_code,
        "elapsed_ms": response.elapsed.total_seconds() * 1000,
        "headers": dict(response.headers),
    }

    # Try to parse JSON body, fall back to text
    try:
        response_data["body"] = response.json()
    except Exception:
        response_data["body"] = response.text[:1000]

    allure.attach(
        json.dumps(response_data, indent=2, default=str),
        name=f"HTTP Response [{response.status_code}]",
        attachment_type=allure.attachment_type.JSON,
    )


def attach_json(data: Any, name: str = "JSON Data") -> None:
    """
    Attach any JSON-serializable data to report.

    Use for:
    - Test data
    - Parsed models
    - Intermediate results

    Args:
        data: Any JSON serializable data
        name: Display name in report
    """
    allure.attach(
        json.dumps(data, indent=2, default=str),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def attach_text(text: str, name: str = "Text") -> None:
    """Attach plain text to report."""
    allure.attach(
        text,
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )


def attach_validation_result(
    schema_name: str,
    passed: bool,
    details: str = "",
) -> None:
    """
    Attach schema validation result to report.

    Args:
        schema_name: Which schema was used
        passed: Did validation pass?
        details: Extra details on failure
    """
    result = {
        "schema": schema_name,
        "result": "✅ PASSED" if passed else "❌ FAILED",
    }
    if details:
        result["details"] = details

    allure.attach(
        json.dumps(result, indent=2),
        name=f"Schema Validation: {schema_name}",
        attachment_type=allure.attachment_type.JSON,
    )