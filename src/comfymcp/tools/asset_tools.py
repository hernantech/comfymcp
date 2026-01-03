"""MCP tools for ComfyUI asset management (images, models, embeddings)."""

import base64
import json
import logging
from typing import Callable

from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent

from comfymcp.client.http import ComfyUIClient, ComfyUIError

logger = logging.getLogger(__name__)

# Map file extensions to MIME types
MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
}


def get_mime_type(filename: str) -> str:
    """Detect MIME type from filename extension."""
    lower_name = filename.lower()
    for ext, mime_type in MIME_TYPES.items():
        if lower_name.endswith(ext):
            return mime_type
    # Default to PNG if unknown
    return "image/png"


def register_asset_tools(server: FastMCP, get_client: Callable[[], ComfyUIClient]) -> None:
    """Register asset management tools with the MCP server.

    Args:
        server: The MCP server instance
        get_client: Callable that returns the ComfyUIClient instance
    """

    @server.tool()
    async def list_models(
        model_type: str = "",
    ) -> list[TextContent]:
        """List available models in ComfyUI.

        Args:
            model_type: Type of models to list (e.g., "checkpoints", "loras", "vae").
                       If empty, returns list of all model types.

        Returns:
            JSON with model type list or models in specified folder.
        """
        client = get_client()

        try:
            if model_type:
                # List models in the specified folder
                models = await client.get_models(model_type)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "model_type": model_type,
                                "models": models,
                                "count": len(models),
                            },
                            indent=2,
                        ),
                    )
                ]
            else:
                # List all model types (folders)
                model_types = await client.get_model_folders()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "model_types": model_types,
                                "count": len(model_types),
                            },
                            indent=2,
                        ),
                    )
                ]
        except ComfyUIError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": str(e),
                            "status_code": e.status_code,
                            "details": e.details,
                        }
                    ),
                )
            ]

    @server.tool()
    async def list_output_images(
        subfolder: str = "",
    ) -> list[TextContent]:
        """List generated images in ComfyUI output folder.

        Note: ComfyUI does not have a direct endpoint to list files.
        This tool uses the history endpoint to extract output images.

        Args:
            subfolder: Optional subfolder to filter images by.

        Returns:
            JSON list of image filenames with metadata.
        """
        client = get_client()

        try:
            # Get history to find output images
            history = await client.get_history()

            images = []
            seen = set()

            for prompt_id, entry in history.items():
                for node_id, node_output in entry.outputs.items():
                    if "images" in node_output:
                        for img in node_output["images"]:
                            filename = img.get("filename", "")
                            img_subfolder = img.get("subfolder", "")
                            img_type = img.get("type", "output")

                            # Filter by subfolder if specified
                            if subfolder and img_subfolder != subfolder:
                                continue

                            # Avoid duplicates
                            key = f"{img_type}/{img_subfolder}/{filename}"
                            if key in seen:
                                continue
                            seen.add(key)

                            images.append(
                                {
                                    "filename": filename,
                                    "subfolder": img_subfolder,
                                    "type": img_type,
                                    "prompt_id": prompt_id,
                                    "node_id": node_id,
                                }
                            )

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "images": images,
                            "count": len(images),
                            "subfolder_filter": subfolder if subfolder else None,
                        },
                        indent=2,
                    ),
                )
            ]
        except ComfyUIError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": str(e),
                            "status_code": e.status_code,
                            "details": e.details,
                        }
                    ),
                )
            ]

    @server.tool()
    async def get_image(
        filename: str,
        subfolder: str = "",
        folder_type: str = "output",
        format: str = "url",
    ) -> list[TextContent | ImageContent]:
        """Get an image from ComfyUI.

        Args:
            filename: Name of the image file.
            subfolder: Subfolder within the folder type.
            folder_type: One of "output", "input", or "temp".
            format: Return format - "url" for URL, "base64" for inline image data.

        Returns:
            Either an image URL (as JSON) or base64-encoded image data.
        """
        client = get_client()

        # Validate folder_type
        if folder_type not in ("output", "input", "temp"):
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": f"Invalid folder_type: {folder_type}",
                            "valid_types": ["output", "input", "temp"],
                        }
                    ),
                )
            ]

        # Validate format
        if format not in ("url", "base64"):
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": f"Invalid format: {format}",
                            "valid_formats": ["url", "base64"],
                        }
                    ),
                )
            ]

        try:
            if format == "base64":
                # Return inline image data
                data = await client.get_image_base64(filename, subfolder, folder_type)
                mime_type = get_mime_type(filename)
                return [
                    ImageContent(
                        type="image",
                        data=data,
                        mimeType=mime_type,
                    )
                ]
            else:
                # Return URL
                url = client.get_image_url(filename, subfolder, folder_type)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "url": url,
                                "filename": filename,
                                "subfolder": subfolder,
                                "folder_type": folder_type,
                            }
                        ),
                    )
                ]
        except ComfyUIError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": str(e),
                            "status_code": e.status_code,
                            "details": e.details,
                        }
                    ),
                )
            ]

    @server.tool()
    async def upload_image(
        image_data: str,
        filename: str,
        folder_type: str = "input",
        overwrite: bool = False,
        subfolder: str = "",
    ) -> list[TextContent]:
        """Upload an image to ComfyUI.

        Args:
            image_data: Base64-encoded image data.
            filename: Desired filename for the uploaded image.
            folder_type: One of "input" or "temp".
            overwrite: Whether to overwrite existing file with same name.
            subfolder: Subfolder to upload the image to.

        Returns:
            JSON with uploaded file info (name, subfolder, type).
        """
        client = get_client()

        # Validate folder_type
        if folder_type not in ("input", "temp"):
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": f"Invalid folder_type: {folder_type}",
                            "valid_types": ["input", "temp"],
                        }
                    ),
                )
            ]

        try:
            # Decode base64 data
            try:
                raw_data = base64.b64decode(image_data)
            except Exception as decode_error:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "Failed to decode base64 image data",
                                "details": str(decode_error),
                            }
                        ),
                    )
                ]

            # Upload the image
            response = await client.upload_image(
                image_data=raw_data,
                filename=filename,
                folder_type=folder_type,
                overwrite=overwrite,
                subfolder=subfolder,
            )

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "name": response.name,
                            "subfolder": response.subfolder,
                            "type": response.type,
                        },
                        indent=2,
                    ),
                )
            ]
        except ComfyUIError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": str(e),
                            "status_code": e.status_code,
                            "details": e.details,
                        }
                    ),
                )
            ]

    @server.tool()
    async def list_embeddings() -> list[TextContent]:
        """List available embeddings in ComfyUI.

        Returns:
            JSON list of embedding names.
        """
        client = get_client()

        try:
            embeddings = await client.get_embeddings()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "embeddings": embeddings,
                            "count": len(embeddings),
                        },
                        indent=2,
                    ),
                )
            ]
        except ComfyUIError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": str(e),
                            "status_code": e.status_code,
                            "details": e.details,
                        }
                    ),
                )
            ]
