# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenEdge Analytics MCP Server - A read-only Model Context Protocol (MCP) server providing analytics data access to QAD/OpenEdge databases. Enables AI clients to query OEE, scrap rates, and customer margins via JSON-RPC over stdin/stdout.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with: ODBC_DSN, DB_USER, DB_PASSWORD, ANALYTICS_SCHEMA

# Run MCP server
python -m mcp_server.server

# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/test_oee_tool.py -v

# Test database connection manually
python -m mcp_server.db.manual_test_connection

# Test OEE query with real data
python -m mcp_server.db.test_oee_query
```

## Architecture

```
Server (JSON-RPC 2.0) → Tools Layer → DB Connection → SQL Templates
```

### Key Components

- **`mcp_server/server.py`**: Async JSON-RPC handler, tool registration and dispatch
- **`mcp_server/config.py`**: Environment-based configuration (`DatabaseConfig`, `AppConfig`)
- **`mcp_server/db/connection.py`**: ODBC wrapper with context managers, singleton pattern
- **`mcp_server/tools/`**: Analytics tool implementations (OEE, Scrap, Margin)
- **`sql_templates/`**: Parameterized SQL queries with `{schema}` placeholders

### Available MCP Tools

| Tool | Function | Key Parameters |
|------|----------|----------------|
| `get_oee_trend` | OEE metrics over time | line_id (work center), from_date, to_date |
| `get_scrap_summary` | Scrap rates by dimension | plant_id, from_date, to_date, group_by |
| `get_margin_by_customer` | Revenue/margin analysis | period, customer_id (optional) |

## OpenEdge-Specific Considerations

- **Column names are UPPERCASE**: Query results return `PRODUCTION_DATE`, `OEE`, etc.
- **No `SELECT 1` support**: Use `SELECT 1 FROM sysprogress.syscalctable` for connection tests
- **Date parameter binding issues**: Use string replacement with validated inputs instead of `?` placeholders
- **`conn.timeout` not supported**: Wrapped in try/except to handle gracefully
- **Use `op_wkctr` not `op_line`**: Work Center field for OEE filtering

## SQL Template Conventions

- Use `{schema}` placeholder (replaced with `ANALYTICS_SCHEMA` env var, default: `PUB`)
- Use `{wkctr}`, `{from_date}`, `{to_date}` for validated string replacement
- Avoid Korean comments in SQL (causes encoding issues with OpenEdge)

## Testing

Tests use mocked pyodbc to run without ODBC drivers. Mock data must use UPPERCASE column names to match OpenEdge behavior.

## Key Tables (QAD Schema)

- `op_hist`: Operation history (OEE, scrap data)
- `ih_hist`: Invoice header history
- `idh_hist`: Invoice detail history
- `cm_mstr`: Customer master
