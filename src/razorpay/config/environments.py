"""
Environment-specific overrides.
Same test might behave differently in staging vs production.
"""

from dataclasses import dataclass
from src.razorpay.config.settings import settings


@dataclass(frozen=True)
class EnvironmentConfig:
    """
    frozen=True means these values cannot be changed after creation.
    Immutable config = no accidental overwrites during test run.
    """
    name: str
    base_url: str
    timeout: int
    max_retries: int
    currency: str


# -------------------------
# Environment Definitions
# -------------------------
STAGING_CONFIG = EnvironmentConfig(
    name="staging",
    base_url="https://api.razorpay.com/v1",
    timeout=30,
    max_retries=3,
    currency="INR",
)

PRODUCTION_CONFIG = EnvironmentConfig(
    name="production",
    base_url="https://api.razorpay.com/v1",
    timeout=60,       # production gets more time
    max_retries=1,    # never retry in production
    currency="INR",
)

DEV_CONFIG = EnvironmentConfig(
    name="dev",
    base_url="https://api.razorpay.com/v1",
    timeout=10,
    max_retries=5,
    currency="INR",
)

# -------------------------
# Config Resolver
# -------------------------
ENV_MAP: dict[str, EnvironmentConfig] = {
    "staging": STAGING_CONFIG,
    "production": PRODUCTION_CONFIG,
    "dev": DEV_CONFIG,
}


def get_environment_config() -> EnvironmentConfig:
    """
    Returns the correct EnvironmentConfig based on .env ENVIRONMENT value.
    
    Usage:
        from src.razorpay.config.environments import get_environment_config
        env_config = get_environment_config()
        env_config.max_retries  # 3 (if staging)
    """
    env_name = settings.environment
    config = ENV_MAP.get(env_name)

    if config is None:
        raise ValueError(
            f"No config found for environment '{env_name}'. "
            f"Available: {list(ENV_MAP.keys())}"
        )

    return config


# Module-level instance
env_config = get_environment_config()