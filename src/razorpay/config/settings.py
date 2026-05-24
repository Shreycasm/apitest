"""
Global settings loaded from .env file.
Pydantic validates every value on startup.
If anything is missing or wrong type → crash immediately with clear error.
"""

from functools import lru_cache
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All config lives here.
    Pydantic reads from .env automatically.
    """

    model_config = SettingsConfigDict(
        env_file=".env",              # which file to read
        env_file_encoding="utf-8",    # encoding
        case_sensitive=False,         # KEY_ID = key_id = same
        extra="ignore",               # ignore unknown env vars
    )

    # -------------------------
    # Razorpay Credentials
    # -------------------------
    razorpay_key_id: str = Field(
        ...,                          # ... means REQUIRED, no default
        description="Razorpay API Key ID"
    )
    razorpay_key_secret: str = Field(
        ...,
        description="Razorpay API Key Secret"
    )

    # -------------------------
    # API Configuration
    # -------------------------
    razorpay_base_url: str = Field(
        default="https://api.razorpay.com/v1",
        description="Razorpay base URL"
    )
    environment: str = Field(
        default="staging",
        description="Environment: staging or production"
    )
    request_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds"
    )

    # -------------------------
    # Validators
    # -------------------------
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Only allow valid environments."""
        allowed = {"staging", "production", "dev"}
        if value.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got '{value}'")
        return value.lower()

    @field_validator("razorpay_key_id")
    @classmethod
    def validate_key_id(cls, value: str) -> str:
        """Razorpay test keys start with rzp_test_"""
        if not value.startswith("rzp_"):
            raise ValueError("razorpay_key_id must start with 'rzp_'")
        return value

    @field_validator("request_timeout")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        """Timeout must be between 5 and 120 seconds."""
        if not (5 <= value <= 120):
            raise ValueError("request_timeout must be between 5 and 120 seconds")
        return value

    # -------------------------
    # Computed Fields
    # (derived from other fields, not from .env)
    # -------------------------
    @computed_field
    @property
    def orders_url(self) -> str:
        """Full URL for orders endpoint."""
        return f"{self.razorpay_base_url}/orders"

    @computed_field
    @property
    def payments_url(self) -> str:
        """Full URL for payments endpoint."""
        return f"{self.razorpay_base_url}/payments"

    @computed_field
    @property
    def refunds_url(self) -> str:
        """Full URL for refunds endpoint."""
        return f"{self.razorpay_base_url}/refunds"

    @computed_field
    @property
    def is_test_environment(self) -> bool:
        """True if running against test/staging environment."""
        return self.razorpay_key_id.startswith("rzp_test_")

    @computed_field
    @property
    def auth(self) -> tuple[str, str]:
        """
        Returns (key_id, key_secret) tuple.
        Razorpay uses HTTP Basic Auth.
        Ready to pass directly into requests.get(auth=settings.auth)
        """
        return (self.razorpay_key_id, self.razorpay_key_secret)


# -------------------------
# THE SINGLE INSTANCE
# -------------------------
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns cached Settings instance.

    lru_cache = .env file is read ONCE at startup.
    Not on every import.
    Fast + efficient.
    """
    return Settings()


# Module-level singleton
# Import this anywhere in the project
settings = get_settings()