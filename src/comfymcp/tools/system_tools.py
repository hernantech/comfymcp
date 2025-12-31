"""MCP tools for ComfyUI system operations."""

import json
from typing import Callable

from mcp.server import Server
from mcp.types import TextContent

from comfymcp.client.http import ComfyUIClient, ComfyUIError


def register_system_tools(server: Server, get_client: Callable[[], ComfyUIClient]) -> None:
    """Register system management tools with the MCP server.

    Args:
        server: The MCP server instance
        get_client: Callable that returns the ComfyUIClient instance
    """

    @server.tool()
    async def get_system_stats() -> list[TextContent]:
        """Get ComfyUI system statistics including GPU and memory info.

        Returns system information (OS, Python version, embedded Python status)
        and device information for each GPU (name, type, VRAM total/free/used).
        """
        client = get_client()
        try:
            stats = await client.get_system_stats()

            # Format device info with human-readable values
            devices = []
            for d in stats.devices:
                vram_total_gb = round(d.vram_total / (1024**3), 2) if d.vram_total > 0 else 0
                vram_free_gb = round(d.vram_free / (1024**3), 2) if d.vram_free > 0 else 0
                vram_used_gb = round((d.vram_total - d.vram_free) / (1024**3), 2) if d.vram_total > 0 else 0
                vram_used_percent = round((1 - d.vram_free / d.vram_total) * 100, 1) if d.vram_total > 0 else 0

                # Torch-specific VRAM tracking (memory allocated by PyTorch)
                torch_vram_total_gb = round(d.torch_vram_total / (1024**3), 2) if d.torch_vram_total > 0 else 0
                torch_vram_free_gb = round(d.torch_vram_free / (1024**3), 2) if d.torch_vram_free > 0 else 0

                devices.append({
                    "name": d.name,
                    "type": d.type,
                    "index": d.index,
                    "vram": {
                        "total_gb": vram_total_gb,
                        "free_gb": vram_free_gb,
                        "used_gb": vram_used_gb,
                        "used_percent": vram_used_percent,
                    },
                    "torch_vram": {
                        "total_gb": torch_vram_total_gb,
                        "free_gb": torch_vram_free_gb,
                    },
                })

            result = {
                "system": stats.system,
                "devices": devices,
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except ComfyUIError as e:
            error_result = {
                "error": str(e),
                "status_code": e.status_code,
                "details": e.details,
            }
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    @server.tool()
    async def free_memory(
        unload_models: bool = False,
        free_memory: bool = True,
    ) -> list[TextContent]:
        """Free memory by unloading models and/or clearing caches.

        Args:
            unload_models: If True, unload all loaded models from memory.
                          Use this when you need to load different models
                          or reclaim significant VRAM.
            free_memory: If True, free memory caches (kept by default for
                        faster reloading). This clears intermediate tensors
                        and cached computations.

        Returns:
            Success status message.
        """
        client = get_client()
        try:
            await client.free_memory(unload_models=unload_models, free_memory=free_memory)

            actions = []
            if unload_models:
                actions.append("unloaded all models")
            if free_memory:
                actions.append("cleared memory caches")

            result = {
                "success": True,
                "actions": actions,
                "message": f"Memory freed: {', '.join(actions)}" if actions else "No actions taken",
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except ComfyUIError as e:
            error_result = {
                "success": False,
                "error": str(e),
                "status_code": e.status_code,
                "details": e.details,
            }
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    @server.tool()
    async def get_extensions() -> list[TextContent]:
        """List all loaded ComfyUI extensions.

        Returns a list of extension paths/names that are currently loaded
        in the ComfyUI server. Extensions provide additional nodes and
        functionality beyond the core ComfyUI nodes.
        """
        client = get_client()
        try:
            extensions = await client.get_extensions()

            result = {
                "count": len(extensions),
                "extensions": extensions,
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except ComfyUIError as e:
            error_result = {
                "error": str(e),
                "status_code": e.status_code,
                "details": e.details,
            }
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    @server.tool()
    async def check_connection() -> list[TextContent]:
        """Check if the ComfyUI server is reachable.

        Attempts to connect to the ComfyUI server and returns the
        connection status along with the server URL. Use this to
        verify the server is running before queuing workflows.
        """
        client = get_client()
        try:
            is_connected = await client.is_connected()

            result = {
                "connected": is_connected,
                "server_url": client.base_url,
                "status": "online" if is_connected else "offline",
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            # Even connection check errors should be handled gracefully
            result = {
                "connected": False,
                "server_url": client.base_url,
                "status": "error",
                "error": str(e),
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
