"""ComfyMCP - MCP server for ComfyUI workflow automation.

This module provides the main MCP server that wraps ComfyUI's APIs,
enabling programmatic workflow construction, execution, and monitoring.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server import Server
from mcp.server.stdio import stdio_server

from comfymcp.client.http import ComfyUIClient
from comfymcp.client.websocket import ComfyUIWebSocket
from comfymcp.resources import register_node_resources, register_output_resources
from comfymcp.tools import (
    register_asset_tools,
    register_builder_tools,
    register_system_tools,
    register_workflow_tools,
)
from comfymcp.workflow.node_defs import NodeDefCache

logger = logging.getLogger(__name__)


class ComfyMCPServer:
    """Main MCP server for ComfyUI integration.

    Manages the lifecycle of:
    - ComfyUI HTTP client for API calls
    - ComfyUI WebSocket client for real-time events
    - Node definition cache for workflow building
    - MCP server with all tools and resources

    Example:
        server = ComfyMCPServer(host="127.0.0.1", port=8188)
        await server.run()
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        api_key: str | None = None,
        auto_refresh_nodes: bool = True,
    ) -> None:
        """Initialize the ComfyMCP server.

        Args:
            host: ComfyUI server host
            port: ComfyUI server port
            api_key: Optional API key for ComfyUI
            auto_refresh_nodes: Whether to refresh node cache on startup
        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.auto_refresh_nodes = auto_refresh_nodes

        # Components (initialized on run)
        self._client: ComfyUIClient | None = None
        self._websocket: ComfyUIWebSocket | None = None
        self._node_cache: NodeDefCache | None = None
        self._mcp_server: Server | None = None

    @property
    def client(self) -> ComfyUIClient:
        """Get the HTTP client instance."""
        if self._client is None:
            raise RuntimeError("Server not started. Call run() first.")
        return self._client

    @property
    def websocket(self) -> ComfyUIWebSocket:
        """Get the WebSocket client instance."""
        if self._websocket is None:
            raise RuntimeError("Server not started. Call run() first.")
        return self._websocket

    @property
    def node_cache(self) -> NodeDefCache:
        """Get the node definition cache."""
        if self._node_cache is None:
            raise RuntimeError("Server not started. Call run() first.")
        return self._node_cache

    def _get_client(self) -> ComfyUIClient:
        """Getter for passing to tool registration."""
        return self.client

    def _get_cache(self) -> NodeDefCache:
        """Getter for passing to resource registration."""
        return self.node_cache

    @asynccontextmanager
    async def _lifespan(self) -> AsyncIterator[None]:
        """Manage the lifecycle of ComfyUI connections."""
        # Initialize components
        self._client = ComfyUIClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
        )
        self._websocket = ComfyUIWebSocket(
            host=self.host,
            port=self.port,
        )
        self._node_cache = NodeDefCache()

        try:
            # Connect to ComfyUI
            await self._client.connect()
            logger.info(f"Connected to ComfyUI at {self.host}:{self.port}")

            # Optionally refresh node cache
            if self.auto_refresh_nodes:
                try:
                    await self._node_cache.refresh(self._client)
                    logger.info(f"Loaded {len(self._node_cache._cache)} node definitions")
                except Exception as e:
                    logger.warning(f"Failed to refresh node cache: {e}")

            yield

        finally:
            # Cleanup
            if self._websocket:
                await self._websocket.disconnect()
            if self._client:
                await self._client.close()
            logger.info("Disconnected from ComfyUI")

    def _setup_server(self) -> Server:
        """Create and configure the MCP server."""
        server = Server("comfymcp")

        # Register all tools
        register_workflow_tools(server, self._get_client)
        register_builder_tools(server, self._get_client)
        register_asset_tools(server, self._get_client)
        register_system_tools(server, self._get_client)

        # Register resources
        register_node_resources(server, self._get_cache)
        register_output_resources(server, self._get_client)

        return server

    async def run(self) -> None:
        """Run the MCP server.

        This starts the server using stdio transport, reading from stdin
        and writing to stdout. The server runs until the connection closes.
        """
        async with self._lifespan():
            self._mcp_server = self._setup_server()

            async with stdio_server() as (read_stream, write_stream):
                await self._mcp_server.run(
                    read_stream,
                    write_stream,
                    self._mcp_server.create_initialization_options(),
                )


def main() -> None:
    """Entry point for the comfymcp command."""
    import os

    # Environment variable defaults
    env_host = os.environ.get("COMFYUI_HOST", "127.0.0.1")
    env_port = int(os.environ.get("COMFYUI_PORT", "8188"))
    env_api_key = os.environ.get("COMFYUI_API_KEY")

    parser = argparse.ArgumentParser(
        description="ComfyMCP - MCP server for ComfyUI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default=env_host,
        help="ComfyUI server host (env: COMFYUI_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=env_port,
        help="ComfyUI server port (env: COMFYUI_PORT)",
    )
    parser.add_argument(
        "--api-key",
        default=env_api_key,
        help="ComfyUI API key (env: COMFYUI_API_KEY)",
    )
    parser.add_argument(
        "--no-auto-refresh",
        action="store_true",
        help="Don't automatically refresh node definitions on startup",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    # Create and run server
    server = ComfyMCPServer(
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        auto_refresh_nodes=not args.no_auto_refresh,
    )

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
