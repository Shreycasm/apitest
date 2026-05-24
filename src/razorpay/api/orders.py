"""
Orders API Layer.

Wraps all Razorpay Orders endpoints:
- POST   /orders              → create_order()
- GET    /orders/{id}         → get_order()
- GET    /orders              → list_orders()
- PATCH  /orders/{id}         → update_order()
- GET    /orders/{id}/payments → get_order_payments()

Each method:
1. Accepts clean Python arguments
2. Builds the request model
3. Makes the HTTP call via base client
4. Parses response into typed model
5. Returns typed model OR raw response
   (raw response for negative tests)
"""

from requests import Response

from src.razorpay.api.base_client import RazorpayClient
from src.razorpay.models.order_model import (
    CreateOrderRequest,
    UpdateOrderRequest,
    OrderResponse,
    OrderListResponse,
    Currency,
)
from src.razorpay.utils.logger import logger


class OrdersAPI:
    """
    All Razorpay Orders API operations.

    Usage:
        orders_api = OrdersAPI()
        order = orders_api.create_order(amount=50000)
        print(order.id)
    """

    # Endpoint constants
    # Never hardcode strings in methods
    _ENDPOINT = "/orders"

    def __init__(self, client: RazorpayClient | None = None) -> None:
        """
        Accept optional client for dependency injection.
        If not provided, creates its own.

        Why dependency injection?
        → In tests, we can pass a mock client
        → In production, it creates real client
        → Flexible and testable
        """
        self._client = client or RazorpayClient()
        self._log = logger.bind(component="OrdersAPI")

    # ─────────────────────────────────────────
    # CREATE ORDER
    # ─────────────────────────────────────────
    def create_order(
        self,
        amount: int,
        currency: Currency = Currency.INR,
        receipt: str | None = None,
        notes: dict[str, str] | None = None,
        partial_payment: bool = False,
    ) -> OrderResponse:
        """
        Create a new Razorpay order.

        Args:
            amount: Amount in paise. 50000 = ₹500
            currency: Currency code. Default INR
            receipt: Your internal receipt number
            notes: Key-value metadata. Max 15 keys
            partial_payment: Allow partial payments

        Returns:
            OrderResponse: Parsed and validated order object

        Raises:
            ValidationError: If response shape is unexpected
            RequestException: If network call fails

        Example:
            order = orders_api.create_order(
                amount=50000,
                receipt="receipt_001",
                notes={"customer": "John"}
            )
            print(order.id)          # order_xxxxx
            print(order.status)      # OrderStatus.CREATED
            print(order.amount_in_rupees)  # 500.0
        """
        # Build validated request model
        request = CreateOrderRequest(
            amount=amount,
            currency=currency,
            receipt=receipt,
            notes=notes or {},
            partial_payment=partial_payment,
        )

        self._log.info(
            "creating_order",
            amount=amount,
            currency=currency.value,
            receipt=receipt,
        )

        # Make API call
        response = self._client.post(
            self._ENDPOINT,
            json=request.to_api_payload(),
        )

        # Parse and return typed model
        return OrderResponse(**response.json())

    def create_order_raw(
        self,
        payload: dict,
    ) -> Response:
        """
        Create order with RAW payload (no validation).

        Use this for NEGATIVE tests where you want to
        send bad data and assert on error responses.

        Args:
            payload: Raw dict, sent as-is to Razorpay

        Returns:
            Raw Response object (not parsed)

        Example:
            response = orders_api.create_order_raw({"amount": -1})
            assert response.status_code == 400
        """
        self._log.info(
            "creating_order_raw",
            payload=payload,
        )
        return self._client.post(self._ENDPOINT, json=payload)

    # ─────────────────────────────────────────
    # GET ORDER
    # ─────────────────────────────────────────
    def get_order(self, order_id: str) -> OrderResponse:
        """
        Fetch a single order by ID.

        Args:
            order_id: Razorpay order ID e.g. "order_xxxxx"

        Returns:
            OrderResponse: Parsed order

        Example:
            order = orders_api.get_order("order_DBJOWzybf0sJbb")
            print(order.status)
        """
        if not order_id:
            raise ValueError("order_id cannot be empty")

        self._log.info("fetching_order", order_id=order_id)

        response = self._client.get(f"{self._ENDPOINT}/{order_id}")
        return OrderResponse(**response.json())

    def get_order_raw(self, order_id: str) -> Response:
        """
        Fetch order with raw response.
        Use for negative tests (invalid IDs, etc.)

        Example:
            response = orders_api.get_order_raw("bad_id")
            assert response.status_code == 400
        """
        self._log.info("fetching_order_raw", order_id=order_id)
        return self._client.get(f"{self._ENDPOINT}/{order_id}")

    # ─────────────────────────────────────────
    # LIST ORDERS
    # ─────────────────────────────────────────
    def list_orders(
        self,
        count: int = 10,
        skip: int = 0,
        from_timestamp: int | None = None,
        to_timestamp: int | None = None,
        authorized: bool | None = None,
        receipt: str | None = None,
    ) -> OrderListResponse:
        """
        Fetch list of orders with optional filters.

        Args:
            count: Number of orders to return. Max 100
            skip: Number of orders to skip (pagination)
            from_timestamp: Unix timestamp. Orders created after this
            to_timestamp: Unix timestamp. Orders created before this
            authorized: Filter by authorized status
            receipt: Filter by receipt number

        Returns:
            OrderListResponse: List of orders + count

        Example:
            orders = orders_api.list_orders(count=5)
            print(orders.count)
            for order in orders.items:
                print(order.id)
        """
        if count > 100:
            raise ValueError(
                f"count cannot exceed 100, got {count}"
            )
        if skip < 0:
            raise ValueError(
                f"skip cannot be negative, got {skip}"
            )

        # Build query params, skip None values
        params: dict = {"count": count, "skip": skip}

        if from_timestamp is not None:
            params["from"] = from_timestamp
        if to_timestamp is not None:
            params["to"] = to_timestamp
        if authorized is not None:
            params["authorized"] = int(authorized)
        if receipt is not None:
            params["receipt"] = receipt

        self._log.info("listing_orders", params=params)

        response = self._client.get(self._ENDPOINT, params=params)
        return OrderListResponse(**response.json())

    def list_orders_raw(self, params: dict | None = None) -> Response:
        """
        List orders with raw response.
        Use for negative tests (invalid params etc.)
        """
        self._log.info("listing_orders_raw", params=params)
        return self._client.get(self._ENDPOINT, params=params)

    # ─────────────────────────────────────────
    # UPDATE ORDER
    # ─────────────────────────────────────────
    def update_order(
        self,
        order_id: str,
        notes: dict[str, str],
    ) -> OrderResponse:
        """
        Update an existing order's notes.
        Only notes can be updated via Razorpay API.

        Args:
            order_id: Order to update
            notes: New notes to set

        Returns:
            OrderResponse: Updated order

        Example:
            order = orders_api.update_order(
                order_id="order_xxxxx",
                notes={"updated": "true"}
            )
        """
        if not order_id:
            raise ValueError("order_id cannot be empty")

        request = UpdateOrderRequest(notes=notes)

        self._log.info(
            "updating_order",
            order_id=order_id,
            notes=notes,
        )

        response = self._client.patch(
            f"{self._ENDPOINT}/{order_id}",
            json=request.to_api_payload(),
        )
        return OrderResponse(**response.json())

    def update_order_raw(
        self,
        order_id: str,
        payload: dict,
    ) -> Response:
        """
        Update order with raw payload.
        Use for negative tests.
        """
        self._log.info(
            "updating_order_raw",
            order_id=order_id,
            payload=payload,
        )
        return self._client.patch(
            f"{self._ENDPOINT}/{order_id}",
            json=payload,
        )


    # ─────────────────────────────────────────
    # Context Manager Support
    # ─────────────────────────────────────────
    def __enter__(self) -> "OrdersAPI":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def close(self) -> None:
        """Close underlying HTTP client."""
        self._client.close()