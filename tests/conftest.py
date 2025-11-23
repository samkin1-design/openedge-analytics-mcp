"""
Pytest configuration and fixtures for OpenEdge Analytics MCP Server tests.

This module sets up mock pyodbc to allow testing without actual ODBC drivers.
"""

import sys
from unittest.mock import MagicMock

import pytest


# Create mock pyodbc module before any imports
mock_pyodbc = MagicMock()
mock_pyodbc.Error = Exception
mock_pyodbc.Connection = MagicMock
mock_pyodbc.Cursor = MagicMock
mock_pyodbc.Row = tuple

# Insert mock into sys.modules
sys.modules["pyodbc"] = mock_pyodbc


@pytest.fixture
def mock_pyodbc_module():
    """Fixture that provides the mock pyodbc module."""
    return mock_pyodbc


@pytest.fixture
def reset_db_connection():
    """Reset the global database connection singleton between tests."""
    from mcp_server.db import connection
    connection._db_connection = None
    yield
    connection._db_connection = None
