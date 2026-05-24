"""
Base HTTP Client.
ALL Razorpay API calls go through this.

Responsibilities:
- Authentication (Basic Auth)
- Request/Response logging
- Timeout management
- Retry logic
- Error handling
- Returns raw Response object (let callers decide what to do)
"""

import time
from typing import Any

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.razorpay.config.settings import settings
from src.razorpay.config.environments import env_config
from src.razorpay.utils.logger import logger
from src.razorpay.utils.allure_helpers import attach_request, attach_response


class RazorpayClient:
    """
    Core HTTP client for Razorpay API.

    Usage:
        client = RazorpayClient()
        response = client.get("/orders")
        response = client.post("/orders", json=payload)
    """

    def __init__(self) -> None:
        self._session = self._build_session()
        self._base_url = settings.razorpay_base_url
        self._timeout = settings.request_timeout
        self._log = logger.bind(component="RazorpayClient")

    # -------------------------
    # Session Builder
    # -------------------------
    def _build_session(self) -> Session:
        """
        Build a requests.Session with:
        - Auth headers set once (not per request)
        - Retry logic with backoff
        - Connection pooling
        """
        session = Session()

        # Basic Auth → Razorpay uses key_id:key_secret
        session.auth = settings.auth

        # Default headers for every request
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "razorpay-automation-framework/1.0.0",
        })

        # Retry Strategy
        # Only retry on network errors and 5xx server errors
        # NEVER retry on 4xx (that's our bug, not server's)
        retry_strategy = Retry(
            total=env_config.max_retries,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH"],
            raise_on_status=False,
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,        # connection pool size
            pool_maxsize=10,
        )

        # Apply adapter to both http and https
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    # -------------------------
    # Core Request Method
    # -------------------------
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Response:
        """
        Central method - every GET/POST/PATCH goes through here.
        Now with Allure attachments for reporting.
        """
        url = f"{self._base_url}{endpoint}"
        start_time = time.perf_counter()

        # Log the outgoing request
        self._log.info(
            "api_request",
            method=method,
            url=url,
            body=kwargs.get("json"),
            params=kwargs.get("params"),
        )

        # Attach request to Allure report
        attach_request(
            method=method,
            url=url,
            body=kwargs.get("json"),
            params=kwargs.get("params"),
        )

        try:
            response = self._session.request(
                method=method,
                url=url,
                timeout=self._timeout,
                **kwargs,
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            self._log.info(
                "api_response",
                method=method,
                url=url,
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size_bytes=len(response.content),
            )

            # Attach response to Allure report
            attach_response(response)

            return response

        except requests.exceptions.ConnectionError as e:
            self._log.error("connection_error", url=url, error=str(e))
            attach_text(f"Connection Error: {e}", name="Error")
            raise

        except requests.exceptions.Timeout as e:
            self._log.error(
                "request_timeout",
                url=url,
                timeout=self._timeout,
                error=str(e)
            )
            attach_text(f"Timeout Error: {e}", name="Error")
            raise

        except requests.exceptions.RequestException as e:
            self._log.error("request_failed", url=url, error=str(e))
            attach_text(f"Request Error: {e}", name="Error")
            raise

    # -------------------------
    # Public HTTP Methods
    # -------------------------
    def get(self, endpoint: str, params: dict | None = None) -> Response:
        """
        HTTP GET request.

        Args:
            endpoint: e.g. "/orders" or "/orders/order_123"
            params: query string params e.g. {"count": 10, "skip": 0}

        Returns:
            Response object
        """
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: dict | None = None) -> Response:
        """
        HTTP POST request.

        Args:
            endpoint: e.g. "/orders"
            json: request body as dict

        Returns:
            Response object
        """
        return self._request("POST", endpoint, json=json)

    def patch(self, endpoint: str, json: dict | None = None) -> Response:
        """
        HTTP PATCH request.

        Args:
            endpoint: e.g. "/orders/order_123"
            json: fields to update

        Returns:
            Response object
        """
        return self._request("PATCH", endpoint, json=json)

    def delete(self, endpoint: str) -> Response:
        """HTTP DELETE request."""
        return self._request("DELETE", endpoint)

    # -------------------------
    # Context Manager Support
    # -------------------------
    def __enter__(self) -> "RazorpayClient":
        """Allow usage with 'with' statement."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Close session when done."""
        self.close()

    def close(self) -> None:
        """Close the HTTP session and free resources."""
        self._session.close()
        self._log.info("session_closed")