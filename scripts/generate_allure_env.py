"""
Generate allure environment.properties file.
Shows environment info in allure report dashboard.
"""

from pathlib import Path
from src.razorpay.config.settings import settings


def generate_environment_file(results_dir: str = "allure-results") -> None:
    """
    Create environment.properties in allure results directory.
    Allure reads this file to show environment info in report.
    """
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)

    env_file = results_path / "environment.properties"

    properties = {
        "Environment": settings.environment,
        "Base.URL": settings.razorpay_base_url,
        "Python.Version": "3.13",
        "Framework": "razorpay-automation/1.0.0",
        "Test.Key.ID": f"{settings.razorpay_key_id[:12]}...",
    }

    with open(env_file, "w") as f:
        for key, value in properties.items():
            f.write(f"{key}={value}\n")

    print(f"✅ Generated {env_file}")


if __name__ == "__main__":
    generate_environment_file()