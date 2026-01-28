# tests/conftest.py
import os

import pytest

# Ensure metrics are disabled in tests
os.environ["ENABLE_METRICS"] = "false"

# Set test environment for consistent test behavior
os.environ["ENVIRONMENT"] = "test"

# Import pytest fixtures from test_app.py
from tests.test_app import app, client  # noqa: F401
