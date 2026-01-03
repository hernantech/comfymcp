"""ComfyMCP - MCP server for ComfyUI workflow automation.

This module provides the main MCP server that wraps ComfyUI's APIs,
enabling programmatic workflow construction, execution, and monitoring.
"""

from __future__ import annotations

import argparse
import logging
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

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


@dataclass
class ComfyUIContext:
    """Context holding ComfyUI client instances."""

    client: ComfyUIClient
    websocket: ComfyUIWebSocket
    node_cache: NodeDefCache


# Global context - set during lifespan
_context: ComfyUIContext | None = None


def get_client() -> ComfyUIClient:
    """Get the ComfyUI HTTP client."""
    if _context is None:
        raise RuntimeError("Server not started")
    return _context.client


def get_cache() -> NodeDefCache:
    """Get the node definition cache."""
    if _context is None:
        raise RuntimeError("Server not started")
    return _context.node_cache


def create_server(
    host: str = "127.0.0.1",
    port: int = 8188,
    api_key: str | None = None,
    auto_refresh_nodes: bool = True,
) -> FastMCP:
    """Create and configure the MCP server.

    Args:
        host: ComfyUI server host
        port: ComfyUI server port
        api_key: Optional API key for ComfyUI
        auto_refresh_nodes: Whether to refresh node cache on startup

    Returns:
        Configured FastMCP server instance
    """

    @asynccontextmanager
    async def lifespan(mcp: FastMCP) -> AsyncIterator[None]:
        """Manage the lifecycle of ComfyUI connections."""
        global _context

        # Initialize components
        client = ComfyUIClient(
            host=host,
            port=port,
            api_key=api_key,
        )
        websocket = ComfyUIWebSocket(
            host=host,
            port=port,
        )
        node_cache = NodeDefCache()

        try:
            # Connect to ComfyUI
            await client.connect()
            logger.info(f"Connected to ComfyUI at {host}:{port}")

            # Optionally refresh node cache
            if auto_refresh_nodes:
                try:
                    await node_cache.refresh(client)
                    logger.info(f"Loaded {len(node_cache._cache)} node definitions")
                except Exception as e:
                    logger.warning(f"Failed to refresh node cache: {e}")

            # Set global context
            _context = ComfyUIContext(
                client=client,
                websocket=websocket,
                node_cache=node_cache,
            )

            yield

        finally:
            # Cleanup
            _context = None
            await websocket.disconnect()
            await client.close()
            logger.info("Disconnected from ComfyUI")

    # Create the FastMCP server with lifespan
    server = FastMCP("comfymcp", lifespan=lifespan)

    # Register all tools
    register_workflow_tools(server, get_client)
    register_builder_tools(server, get_client)
    register_asset_tools(server, get_client)
    register_system_tools(server, get_client)

    # Register resources
    register_node_resources(server, get_cache)
    register_output_resources(server, get_client)

    return server


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

    # Create server
    server = create_server(
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        auto_refresh_nodes=not args.no_auto_refresh,
    )

    try:
        # Run with stdio transport
        server.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
