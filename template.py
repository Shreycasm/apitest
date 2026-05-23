from pathlib import Path


list_of_files = [
    "src/razorpay/__init__.py",
    "src/razorpay/api/__init__.py",
    "src/razorpay/config/__init__.py",

    "src/razorpay/models/__init__.py",
    "src/razorpay/utils/__init__.py",
    "tests/__init__.py",
    "tests/orders/__init__.py",
    "tests/payments/__init__.py",
    "tests/refund/__init__.py",
    "test_data/orders",
    "test_data/schemas",
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

        