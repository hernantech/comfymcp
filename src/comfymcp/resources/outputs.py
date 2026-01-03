"""MCP resources for ComfyUI output images."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Callable

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from comfymcp.client.http import ComfyUIClient


def register_output_resources(
    server: FastMCP,
    get_client: Callable[[], ComfyUIClient],
) -> None:
    """Register output image resources with the MCP server.

    Provides resources for accessing ComfyUI outputs:
    - comfyui://outputs - List recent outputs (from history)
    - comfyui://outputs/{prompt_id} - Outputs from a specific execution
    - comfyui://images/{filename} - Specific image (with query params)

    Args:
        server: The FastMCP server instance
        get_client: Callable that returns the ComfyUIClient instance
    """

    @server.resource("comfyui://outputs", name="Recent Outputs", mime_type="application/json")
    async def list_recent_outputs() -> str:
        """List of recent workflow execution outputs."""
        client = get_client()

        try:
            history = await client.get_history(max_items=20)

            entries = []
            for prompt_id, entry in history.items():
                # Collect image outputs
                images = []
                for node_id, output in entry.outputs.items():
                    if "images" in output:
                        for img in output["images"]:
                            images.append({
                                "filename": img.get("filename", ""),
                                "subfolder": img.get("subfolder", ""),
                                "type": img.get("type", "output"),
                                "node_id": node_id,
                            })

                entries.append({
                    "prompt_id": prompt_id,
                    "status": entry.status.get("status_str") if entry.status else "unknown",
                    "image_count": len(images),
                    "images": images[:5],  # First 5 images
                })

            return json.dumps({
                "count": len(entries),
                "outputs": entries,
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "error_type": type(e).__name__,
            }, indent=2)

    @server.resource("comfyui://outputs/{prompt_id}", name="Execution Output", mime_type="application/json")
    async def get_execution_outputs(prompt_id: str) -> str:
        """Get outputs from a specific execution."""
        client = get_client()

        try:
            history = await client.get_history(prompt_id=prompt_id)

            if prompt_id not in history:
                return json.dumps({
                    "error": f"Execution not found: {prompt_id}",
                }, indent=2)

            entry = history[prompt_id]

            # Collect all outputs by node
            node_outputs = {}
            for node_id, output in entry.outputs.items():
                node_outputs[node_id] = {
                    "type": "images" if "images" in output else "other",
                }

                if "images" in output:
                    node_outputs[node_id]["images"] = [
                        {
                            "filename": img.get("filename", ""),
                            "subfolder": img.get("subfolder", ""),
                            "type": img.get("type", "output"),
                            "uri": f"comfyui://images/{img.get('filename', '')}",
                            "view_url": client.get_image_url(
                                img.get("filename", ""),
                                img.get("subfolder", ""),
                                img.get("type", "output"),
                            ),
                        }
                        for img in output["images"]
                    ]

            return json.dumps({
                "prompt_id": prompt_id,
                "status": entry.status.get("status_str") if entry.status else "unknown",
                "completed": entry.status.get("completed", False) if entry.status else False,
                "outputs": node_outputs,
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "error_type": type(e).__name__,
            }, indent=2)

    @server.resource("comfyui://images/{filename}", name="Image", mime_type="image/png")
    async def get_image(filename: str) -> bytes:
        """Get a specific image as binary data."""
        client = get_client()

        # Default to output folder, no subfolder
        # Note: FastMCP resources don't support query parameters well,
        # so we default to output folder
        image_data = await client.get_image(filename, "", "output")
        return image_data
