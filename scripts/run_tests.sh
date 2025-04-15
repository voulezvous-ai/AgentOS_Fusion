#!/bin/bash
set -e

export PYTHONPATH=$(pwd)
export TEST_REDIS_URL="redis://localhost:6379/1"
export MONGODB_URI="mongodb://localhost:27017/test_promptos_db"
export JWT_SECRET_KEY="test_secret_for_ci_cd"

echo "--- Running Tests ---"
pytest -v -s tests/ --cov=app --cov-report=term-missing

# Optional: linting
# echo "--- Running Linters ---"
# ruff check .
# ruff format . --check

echo "--- Tests Finished ---"
