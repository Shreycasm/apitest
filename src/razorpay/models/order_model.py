"""
Pydantic models for Razorpay Orders API.

Three types of models:
1. Request models  → what WE send to Razorpay
2. Response models → what RAZORPAY sends back
3. Collection models → list responses
"""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


# -------------------------
# Enums
# (fixed set of allowed values)
# -------------------------

class OrderStatus(str, Enum):
    """
    All possible order statuses from Razorpay.
    str + Enum means: value IS the string.
    OrderStatus.CREATED == "created" → True
    """
    CREATED = "created"
    ATTEMPTED = "attempted"
    PAID = "paid"


class Currency(str, Enum):
    """Supported currencies."""
    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    SGD = "SGD"
    AED = "AED"


# -------------------------
# Request Models
# (what we send TO Razorpay)
# -------------------------

class CreateOrderRequest(BaseModel):
    """
    Payload to create a new order.
    Razorpay docs: POST /orders

    Amount is in paise (smallest currency unit)
    So 50000 paise = ₹500
    """

    amount: int = Field(
        ...,
        gt=0,                     # must be greater than 0
        le=10_000_000_00,         # max 10 crore in paise
        description="Amount in paise. 50000 = ₹500",
        examples=[50000],
    )
    currency: Currency = Field(
        default=Currency.INR,
        description="Currency code",
    )
    receipt: str | None = Field(
        default=None,
        max_length=40,
        description="Receipt number for your reference",
        examples=["receipt_001"],
    )
    notes: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value notes. Max 15 keys.",
    )
    partial_payment: bool = Field(
        default=False,
        description="Allow partial payments",
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: dict) -> dict:
        """Razorpay allows max 15 note key-value pairs."""
        if len(value) > 15:
            raise ValueError(
                f"notes can have max 15 keys, got {len(value)}"
            )
        return value

    @field_validator("receipt")
    @classmethod
    def validate_receipt(cls, value: str | None) -> str | None:
        """Receipt must be alphanumeric + underscores only."""
        if value is not None and not value.replace("_", "").replace("#", "").isalnum():
            raise ValueError(
                "receipt must be alphanumeric with _ or # only"
            )
        return value

    def to_api_payload(self) -> dict[str, Any]:
        """
        Convert to dict ready for API call.
        Excludes None values (Razorpay doesn't want null fields).
        """
        return self.model_dump(
            exclude_none=True,
            mode="json",          # convert enums to their values
        )


class UpdateOrderRequest(BaseModel):
    """
    Payload to update an existing order.
    Razorpay docs: PATCH /orders/{id}
    Only notes can be updated.
    """
    notes: dict[str, str] = Field(
        ...,
        description="Updated notes",
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: dict) -> dict:
        if len(value) > 15:
            raise ValueError("notes can have max 15 keys")
        return value

    def to_api_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


# -------------------------
# Response Models
# (what Razorpay sends BACK)
# -------------------------

class OrderResponse(BaseModel):
    """
    Maps exactly to Razorpay order response.
    Every field typed and validated on parse.
    """

    id: str = Field(
        ...,
        description="Razorpay order ID",
        examples=["order_DBJOWzybf0sJbb"],
    )
    entity: str = Field(
        default="order",
        description="Always 'order' for order responses",
    )
    amount: int = Field(
        ...,
        gt=0,
        description="Order amount in paise",
    )
    amount_paid: int | None = Field(
        default=0,
        ge=0,
        description="Amount paid so far in paise",
    )
    amount_due: int = Field(
        ...,
        ge=0,
        description="Amount remaining to be paid",
    )
    currency: Currency = Field(
        ...,
        description="Currency code",
    )
    receipt: str | None = Field(
        default=None,
        description="Receipt number",
    )
    status: OrderStatus = Field(
        ...,
        description="Current order status",
    )
    attempts: int = Field(
        default=0,
        ge=0,
        description="Number of payment attempts",
    )
    notes: list | dict = Field(
        default_factory=list,
        description="Notes attached to order",
    )
    created_at: int = Field(
        ...,
        description="Unix timestamp of creation",
    )

    @model_validator(mode="after")
    def validate_amounts(self) -> "OrderResponse":

        paid = self.amount_paid or 0

        if paid + self.amount_due != self.amount:
            raise ValueError(
                f"amount_paid ({paid}) + "
                f"amount_due ({self.amount_due}) "
                f"must equal amount ({self.amount})"
            )

        return self

    # -------------------------
    # Computed Helper Properties
    # -------------------------
    @property
    def amount_in_rupees(self) -> float:
        """Convert paise to rupees for readable output."""
        return self.amount / 100

    @property
    def created_at_datetime(self) -> datetime:
        """Convert unix timestamp to datetime object."""
        return datetime.fromtimestamp(self.created_at)

    @property
    def is_paid(self) -> bool:
        """True if order is fully paid."""
        return self.status == OrderStatus.PAID

    @property
    def is_created(self) -> bool:
        """True if order is freshly created, no payment attempted."""
        return self.status == OrderStatus.CREATED


class OrderListResponse(BaseModel):
    """
    Response when fetching list of orders.
    Razorpay wraps all lists in this envelope.
    """
    entity: str = Field(default="collection")
    count: int = Field(default=0, ge=0)
    items: list[OrderResponse] = Field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """True if no orders returned."""
        return self.count == 0

    @property
    def order_ids(self) -> list[str]:
        """Extract just the IDs from all orders."""
        return [order.id for order in self.items]