"""
Database connection module for OpenEdge Analytics MCP Server.
"""

from .connection import get_connection, DatabaseConnection

__all__ = ["get_connection", "DatabaseConnection"]
