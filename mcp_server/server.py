"""
OpenEdge Analytics MCP Server Entry Point.

This MCP server provides read-only analytics tools for QAD/OpenEdge databases.
It communicates via standard input/output using JSON-RPC protocol.

Run with: python -m mcp_server.server
"""

import asyncio
import json
import logging
import sys
from typing import Any, Callable, Dict, List, Optional

from mcp_server.tools import get_oee_trend, get_scrap_summary, get_margin_by_customer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


class MCPError(Exception):
    """MCP protocol error."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


# Standard JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPServer:
    """
    MCP Server for OpenEdge Analytics.

    Implements the Model Context Protocol for read-only analytics queries.
    """

    def __init__(self):
        """Initialize the MCP server with registered tools."""
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available MCP tools."""
        # Tool: get_oee_trend
        self.tools["get_oee_trend"] = {
            "name": "get_oee_trend",
            "description": "특정 라인(line_id)의 기간별 OEE(Overall Equipment Effectiveness) 트렌드를 조회합니다. "
            "OEE는 가용성(Availability), 성능(Performance), 품질(Quality)의 곱으로 계산됩니다.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "line_id": {
                        "type": "string",
                        "description": "생산 라인 ID (예: LINE_01)",
                    },
                    "from_date": {
                        "type": "string",
                        "description": "조회 시작일 (ISO 날짜 형식: YYYY-MM-DD)",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "조회 종료일 (ISO 날짜 형식: YYYY-MM-DD)",
                    },
                },
                "required": ["line_id", "from_date", "to_date"],
            },
            "handler": get_oee_trend,
        }

        # Tool: get_scrap_summary
        self.tools["get_scrap_summary"] = {
            "name": "get_scrap_summary",
            "description": "특정 공장(plant_id)의 기간별 Scrap(불량) 요약을 조회합니다. "
            "제품별, 작업장별, 공정별로 그룹화하여 조회할 수 있습니다.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "plant_id": {
                        "type": "string",
                        "description": "공장 ID (예: PLANT_A)",
                    },
                    "from_date": {
                        "type": "string",
                        "description": "조회 시작일 (ISO 날짜 형식: YYYY-MM-DD)",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "조회 종료일 (ISO 날짜 형식: YYYY-MM-DD)",
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["product", "workcenter", "operation"],
                        "description": "그룹화 기준 (product: 제품별, workcenter: 작업장별, operation: 공정별)",
                    },
                },
                "required": ["plant_id", "from_date", "to_date", "group_by"],
            },
            "handler": get_scrap_summary,
        }

        # Tool: get_margin_by_customer
        self.tools["get_margin_by_customer"] = {
            "name": "get_margin_by_customer",
            "description": "특정 기간 동안 고객별 매출, 원가, 마진 요약을 조회합니다. "
            "특정 고객만 조회하거나 전체 고객 요약을 볼 수 있습니다.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "조회 기간 (예: '2024-01' 또는 '2024Q1')",
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "고객 ID (선택사항, 없으면 전체 고객 요약)",
                    },
                },
                "required": ["period"],
            },
            "handler": get_margin_by_customer,
        }

    def _format_error_response(
        self, request_id: Any, code: int, message: str, data: Any = None
    ) -> Dict[str, Any]:
        """Format a JSON-RPC error response."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": request_id, "error": error}

    def _format_success_response(
        self, request_id: Any, result: Any
    ) -> Dict[str, Any]:
        """Format a JSON-RPC success response."""
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "openedge-analytics-mcp",
                "version": "0.1.0",
            },
        }

    def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools_list = []
        for tool_name, tool_def in self.tools.items():
            tools_list.append({
                "name": tool_def["name"],
                "description": tool_def["description"],
                "inputSchema": tool_def["inputSchema"],
            })
        return {"tools": tools_list}

    def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            raise MCPError(
                METHOD_NOT_FOUND,
                f"Tool not found: {tool_name}",
            )

        tool = self.tools[tool_name]
        handler = tool["handler"]

        try:
            result = handler(**arguments)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2),
                    }
                ],
            }
        except TypeError as e:
            raise MCPError(
                INVALID_PARAMS,
                f"Invalid parameters for tool {tool_name}: {str(e)}",
            )
        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            raise MCPError(
                INTERNAL_ERROR,
                f"Tool execution error: {str(e)}",
            )

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming MCP request.

        Args:
            request: JSON-RPC request dictionary.

        Returns:
            JSON-RPC response dictionary.
        """
        request_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "notifications/initialized":
                # This is a notification, no response needed
                return None
            elif method == "tools/list":
                result = self._handle_tools_list(params)
            elif method == "tools/call":
                result = self._handle_tools_call(params)
            else:
                raise MCPError(METHOD_NOT_FOUND, f"Method not found: {method}")

            return self._format_success_response(request_id, result)

        except MCPError as e:
            return self._format_error_response(request_id, e.code, e.message, e.data)
        except Exception as e:
            logger.exception(f"Unexpected error handling request: {method}")
            return self._format_error_response(
                request_id, INTERNAL_ERROR, f"Internal error: {str(e)}"
            )


async def read_message(reader: asyncio.StreamReader) -> Optional[Dict[str, Any]]:
    """Read a single message from the input stream."""
    # Read Content-Length header
    header_line = await reader.readline()
    if not header_line:
        return None

    header = header_line.decode("utf-8").strip()
    if not header.startswith("Content-Length:"):
        logger.error(f"Invalid header: {header}")
        return None

    content_length = int(header.split(":")[1].strip())

    # Read empty line separator
    await reader.readline()

    # Read content
    content = await reader.read(content_length)
    if not content:
        return None

    try:
        return json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return None


def write_message(message: Dict[str, Any]) -> None:
    """Write a message to stdout."""
    content = json.dumps(message, ensure_ascii=False)
    content_bytes = content.encode("utf-8")
    sys.stdout.write(f"Content-Length: {len(content_bytes)}\r\n\r\n")
    sys.stdout.write(content)
    sys.stdout.flush()


async def main() -> None:
    """Main entry point for the MCP server."""
    logger.info("Starting OpenEdge Analytics MCP Server")

    server = MCPServer()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    loop = asyncio.get_event_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    logger.info("MCP Server ready, waiting for requests...")

    while True:
        try:
            message = await read_message(reader)
            if message is None:
                logger.info("End of input, shutting down")
                break

            logger.debug(f"Received: {message.get('method', 'unknown')}")
            response = server.handle_request(message)

            if response is not None:
                write_message(response)

        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
            break

    logger.info("MCP Server shutdown complete")


def run() -> None:
    """Run the MCP server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
