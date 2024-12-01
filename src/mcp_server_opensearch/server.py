from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from mcp_server_opensearch.tools import handle_search

from mcp_server_opensearch.models import Tools

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

server = Server("mcp-server-opensearch")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="search",
            description="Search for a query in the opensearch and return the results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "body": {"type": "object", "description": "Query body following OpenSearch Query DSL"},
                    "index_pattern":
                        {"type": "string",
                         "description": "Comma-separated list of data streams, indexes,"
                                        " and aliases to search. Supports wildcards (`*`)."
                                        " To search all data streams and indexes, omit this parameter "
                                        "or use `*` or `_all`."},
                    "routing": {"type": "string", "description": "Routing value for the query"}
                },
                "required": ["body"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(
        name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    match name:
        case Tools.SEARCH:
            return handle_search(arguments)
        case _:
            raise ValueError(f"Unknown tool: {name}")


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-server-opensearch",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(tools_changed=True),
                    experimental_capabilities={},
                ),
            ),
        )
