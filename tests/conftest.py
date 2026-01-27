# tests/conftest.py
import pytest
import os

# Ensure metrics are disabled in tests
os.environ['ENABLE_METRICS'] = 'false'

# Import pytest fixtures from test_app.py
from tests.test_app import app, client  # noqa: F401