# Razorpay API Automation Framework

Industry-level API testing framework for Razorpay Orders, Payments, and Refunds APIs.

## 🏗️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.13 | Language |
| uv | Package manager |
| pytest | Test runner |
| requests | HTTP client |
| pydantic | Data validation |
| allure | Reporting |
| structlog | Logging |
| pytest-xdist | Parallel execution |
| GitHub Actions | CI/CD |

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Razorpay test account

### Setup
```bash
git clone https://github.com/YOUR_USERNAME/razorpay_automation.git
cd razorpay_automation

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your Razorpay test keys