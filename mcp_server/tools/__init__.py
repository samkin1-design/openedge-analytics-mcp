"""
MCP Tools for OpenEdge Analytics.

All tools are read-only and designed for analytics queries.
"""

from .oee_tools import get_oee_trend
from .scrap_tools import get_scrap_summary
from .margin_tools import get_margin_by_customer

__all__ = [
    "get_oee_trend",
    "get_scrap_summary",
    "get_margin_by_customer",
]
