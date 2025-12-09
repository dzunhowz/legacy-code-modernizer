"""Test configuration."""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring AWS"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
