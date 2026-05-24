.PHONY: test smoke regression report clean parallel parallel-smoke

# Run all tests (sequential)
test:
	uv run pytest -v

# Run all tests (parallel - 4 workers)
parallel:
	uv run pytest -v -n 4

# Run with auto-detected worker count
parallel-auto:
	uv run pytest -v -n auto

# Parallel smoke tests
parallel-smoke:
	uv run pytest -v -n auto -m smoke

# Parallel regression
parallel-regression:
	uv run pytest -v -n auto -m regression

# Parallel with rerun on failure
parallel-safe:
	uv run pytest -v -n auto --reruns 2 --reruns-delay 1

# Run smoke tests only (sequential)
smoke:
	uv run pytest -v -m smoke

# Run regression tests
regression:
	uv run pytest -v -m regression

# Run negative tests
negative:
	uv run pytest -v -m negative

# Run tests and generate allure report
report:
	uv run pytest -v --alluredir=allure-results
	allure generate allure-results --clean -o allure-report
	allure open allure-report

# Parallel with allure report
report-parallel:
	uv run pytest -v -n auto --alluredir=allure-results
	allure generate allure-results --clean -o allure-report
	allure open allure-report

# Generate report without opening
report-generate:
	uv run pytest -v --alluredir=allure-results
	allure generate allure-results --clean -o allure-report

# Open existing report
report-open:
	allure open allure-report

# Serve report (live reload)
report-serve:
	allure serve allure-results

# Clean all generated files
clean:
	rm -rf allure-results allure-report .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf logs/*.log
	@echo "✅ Cleaned"

# Run specific test file
# Usage: make file FILE=tests/orders/test_create_order.py
file:
	uv run pytest $(FILE) -v

# Show test count without running
count:
	uv run pytest --collect-only -q | tail -1