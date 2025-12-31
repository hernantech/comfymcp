"""MCP resources for ComfyUI output images."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Callable
from urllib.parse import parse_qs, unquote, urlparse

from mcp.server import Server
from mcp.types import (
    BlobResourceContents,
    Resource,
    TextResourceContents,
)

if TYPE_CHECKING:
    from comfymcp.client.http import ComfyUIClient


def register_output_resources(
    server: Server,
    get_client: Callable[[], ComfyUIClient],
) -> None:
    """Register output image resources with the MCP server.

    Provides resources for accessing ComfyUI outputs:
    - comfyui://outputs - List recent outputs (from history)
    - comfyui://outputs/{prompt_id} - Outputs from a specific execution
    - comfyui://images/{filename}?type=output - Specific image

    Args:
        server: The MCP server instance
        get_client: Callable that returns the ComfyUIClient instance
    """

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available output resources."""
        resources = [
            Resource(
                uri="comfyui://outputs",
                name="Recent Outputs",
                description="List of recent workflow execution outputs",
                mimeType="application/json",
            ),
        ]

        # Try to add recent history entries
        client = get_client()
        try:
            history = await client.get_history(max_items=10)
            for prompt_id in history:
                resources.append(
                    Resource(
                        uri=f"comfyui://outputs/{prompt_id}",
                        name=f"Output: {prompt_id[:8]}...",
                        description=f"Outputs from execution {prompt_id}",
                        mimeType="application/json",
                    )
                )
        except Exception:
            # If we can't connect, just return the base resources
            pass

        return resources

    @server.read_resource()
    async def read_resource(uri: str) -> TextResourceContents | BlobResourceContents:
        """Read an output resource by URI."""
        client = get_client()

        try:
            parsed = urlparse(uri)

            if uri == "comfyui://outputs":
                return await _list_recent_outputs(uri, client)
            elif parsed.path.startswith("//outputs/"):
                prompt_id = unquote(parsed.path.replace("//outputs/", ""))
                return await _get_execution_outputs(uri, client, prompt_id)
            elif parsed.path.startswith("//images/"):
                filename = unquote(parsed.path.replace("//images/", ""))
                query = parse_qs(parsed.query)
                folder_type = query.get("type", ["output"])[0]
                subfolder = query.get("subfolder", [""])[0]
                return await _get_image(uri, client, filename, subfolder, folder_type)
            else:
                return TextResourceContents(
                    uri=uri,
                    mimeType="application/json",
                    text=json.dumps({"error": f"Unknown resource: {uri}"}, indent=2),
                )
        except Exception as e:
            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({
                    "error": str(e),
                    "error_type": type(e).__name__,
                }, indent=2),
            )


async def _list_recent_outputs(uri: str, client: ComfyUIClient) -> TextResourceContents:
    """List recent workflow outputs from history."""
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

    return TextResourceContents(
        uri=uri,
        mimeType="application/json",
        text=json.dumps({
            "count": len(entries),
            "outputs": entries,
        }, indent=2),
    )


async def _get_execution_outputs(
    uri: str,
    client: ComfyUIClient,
    prompt_id: str,
) -> TextResourceContents:
    """Get outputs from a specific execution."""
    history = await client.get_history(prompt_id=prompt_id)

    if prompt_id not in history:
        return TextResourceContents(
            uri=uri,
            mimeType="application/json",
            text=json.dumps({
                "error": f"Execution not found: {prompt_id}",
            }, indent=2),
        )

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
                    "uri": f"comfyui://images/{img.get('filename', '')}?type={img.get('type', 'output')}&subfolder={img.get('subfolder', '')}",
                    "view_url": client.get_image_url(
                        img.get("filename", ""),
                        img.get("subfolder", ""),
                        img.get("type", "output"),
                    ),
                }
                for img in output["images"]
            ]

    return TextResourceContents(
        uri=uri,
        mimeType="application/json",
        text=json.dumps({
            "prompt_id": prompt_id,
            "status": entry.status.get("status_str") if entry.status else "unknown",
            "completed": entry.status.get("completed", False) if entry.status else False,
            "outputs": node_outputs,
        }, indent=2),
    )


async def _get_image(
    uri: str,
    client: ComfyUIClient,
    filename: str,
    subfolder: str,
    folder_type: str,
) -> BlobResourceContents:
    """Get a specific image as binary data."""
    image_data = await client.get_image(filename, subfolder, folder_type)

    # Determine MIME type from filename
    mime_type = "image/png"  # Default
    if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
        mime_type = "image/jpeg"
    elif filename.lower().endswith(".webp"):
        mime_type = "image/webp"
    elif filename.lower().endswith(".gif"):
        mime_type = "image/gif"

    return BlobResourceContents(
        uri=uri,
        mimeType=mime_type,
        blob=base64.b64encode(image_data).decode("utf-8"),
    )
