from pathlib import Path


list_of_files = [
    "src/razorpay/__init__.py",
    "src/razorpay/api/__init__.py",
    "src/razorpay/api/base_client.py",
    "src/razorpay/api/orders.py",
    "src/razorpay/config/__init__.py",
    "src/razorpay/config/settings.py",
    "src/razorpay/config/environments.py",
    "src/razorpay/models/__init__.py",
    "src/razorpay/models/order_model.py",
    "src/razorpay/utils/__init__.py",
    "src/razorpay/utils/logger.py",
    "src/razorpay/utils/log_context.py",
    "src/razorpay/utils/validators.py",
    "src/razorpay/utils/allure_helpers.py",
    "src/razorpay/utils/test_helpers.py",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/orders/__init__.py",
    "tests/orders/conftest.py",
    "tests/orders/test_create_order.py",
    "tests/orders/test_get_order.py",
    "tests/orders/test_list_orders.py",
    "tests/orders/test_update_order.py",
    "tests/orders/test_order_schema.py",
    "tests/test_parallel_safety.py",
    "test_data/orders",
    "test_data/schemas",
    "test_data/schemas/order_schema.json",
    "test_data/schemas/order_list_schema.json",
    "test_data/schemas/error_schema.json",
    "test_data/allure_categories.json",
    "reports",
    "logs",
    ".github/workflows",
    ".env.example",
    ".env"
]

for file_path in list_of_files:
    path = Path(file_path)

    if path.name.startswith(".") or path.suffix:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    else:
        path.mkdir(parents=True, exist_ok=True)

        