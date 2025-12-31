"""HTTP client for ComfyUI REST API."""

import base64
import json
import logging
from typing import Any
from urllib.parse import urlencode

import aiohttp

from comfymcp.client.types import (
    HistoryEntry,
    NodeDef,
    NodeInputSpec,
    NodeOutputSpec,
    QueueItem,
    QueueResponse,
    QueueStatus,
    SystemStats,
    UploadResponse,
)

logger = logging.getLogger(__name__)


class ComfyUIError(Exception):
    """Base exception for ComfyUI API errors."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class ComfyUIClient:
    """Async HTTP client for ComfyUI API."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = f"http://{host}:{port}"
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "ComfyUIClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self) -> None:
        """Initialize the HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("Client not connected. Call connect() first or use async with.")
        return self._session

    def _headers(self) -> dict[str, str]:
        """Get headers for requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Any = None,
        data: Any = None,
        params: dict | None = None,
    ) -> Any:
        """Make an HTTP request to the ComfyUI API."""
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"

        headers = self._headers() if json_data else {}

        try:
            async with self.session.request(
                method,
                url,
                json=json_data,
                data=data,
                headers=headers,
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    try:
                        error_data = json.loads(error_text)
                    except json.JSONDecodeError:
                        error_data = error_text
                    raise ComfyUIError(
                        f"API error: {response.status}",
                        status_code=response.status,
                        details=error_data,
                    )

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                return await response.read()

        except aiohttp.ClientError as e:
            raise ComfyUIError(f"Connection error: {e}") from e

    # ==================== Prompt/Queue Operations ====================

    async def queue_prompt(
        self,
        workflow: dict[str, Any],
        client_id: str | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> QueueResponse:
        """Queue a workflow for execution.

        Args:
            workflow: The workflow in API format (node_id -> {class_type, inputs})
            client_id: Optional client ID for WebSocket correlation
            extra_data: Optional extra data (e.g., api_key_comfy_org)

        Returns:
            QueueResponse with prompt_id and queue number
        """
        payload: dict[str, Any] = {"prompt": workflow}
        if client_id:
            payload["client_id"] = client_id
        if extra_data:
            payload["extra_data"] = extra_data

        result = await self._request("POST", "/prompt", json_data=payload)
        return QueueResponse(
            prompt_id=result.get("prompt_id", ""),
            number=result.get("number", 0),
            node_errors=result.get("node_errors", {}),
        )

    async def get_queue(self) -> QueueStatus:
        """Get the current queue status."""
        result = await self._request("GET", "/queue")

        def parse_items(items: list) -> list[QueueItem]:
            return [
                QueueItem(
                    number=item[0],
                    prompt_id=item[1],
                    prompt=item[2] if len(item) > 2 else {},
                    extra_data=item[3] if len(item) > 3 else {},
                )
                for item in items
            ]

        return QueueStatus(
            running=parse_items(result.get("queue_running", [])),
            pending=parse_items(result.get("queue_pending", [])),
        )

    async def clear_queue(self) -> None:
        """Clear all pending items from the queue."""
        await self._request("POST", "/queue", json_data={"clear": True})

    async def delete_queue_item(self, prompt_id: str) -> None:
        """Delete a specific item from the queue."""
        await self._request("POST", "/queue", json_data={"delete": [prompt_id]})

    async def interrupt(self) -> None:
        """Interrupt the currently executing prompt."""
        await self._request("POST", "/interrupt")

    # ==================== History Operations ====================

    async def get_history(
        self,
        prompt_id: str | None = None,
        max_items: int | None = None,
    ) -> dict[str, HistoryEntry]:
        """Get execution history.

        Args:
            prompt_id: Get history for a specific prompt
            max_items: Maximum number of history items to return

        Returns:
            Dictionary mapping prompt_id to HistoryEntry
        """
        if prompt_id:
            result = await self._request("GET", f"/history/{prompt_id}")
        else:
            params = {}
            if max_items:
                params["max_items"] = str(max_items)
            result = await self._request("GET", "/history", params=params if params else None)

        return {
            pid: HistoryEntry.from_dict(pid, data)
            for pid, data in result.items()
        }

    async def delete_history(self, prompt_id: str | None = None) -> None:
        """Delete history entries.

        Args:
            prompt_id: Delete specific entry, or all if None
        """
        if prompt_id:
            await self._request("POST", "/history", json_data={"delete": [prompt_id]})
        else:
            await self._request("POST", "/history", json_data={"clear": True})

    # ==================== View/Image Operations ====================

    async def get_image(
        self,
        filename: str,
        subfolder: str = "",
        folder_type: str = "output",
    ) -> bytes:
        """Get an image file.

        Args:
            filename: Name of the image file
            subfolder: Subfolder within the type folder
            folder_type: "output", "input", or "temp"

        Returns:
            Raw image bytes
        """
        params = {
            "filename": filename,
            "type": folder_type,
        }
        if subfolder:
            params["subfolder"] = subfolder

        return await self._request("GET", "/view", params=params)

    async def get_image_base64(
        self,
        filename: str,
        subfolder: str = "",
        folder_type: str = "output",
    ) -> str:
        """Get an image file as base64.

        Returns:
            Base64 encoded image string
        """
        data = await self.get_image(filename, subfolder, folder_type)
        return base64.b64encode(data).decode("utf-8")

    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        folder_type: str = "input",
        overwrite: bool = False,
        subfolder: str = "",
    ) -> UploadResponse:
        """Upload an image file.

        Args:
            image_data: Raw image bytes
            filename: Desired filename
            folder_type: "input" or "temp"
            overwrite: Whether to overwrite existing file
            subfolder: Subfolder to upload to

        Returns:
            UploadResponse with final name and location
        """
        form = aiohttp.FormData()
        form.add_field("image", image_data, filename=filename)
        form.add_field("type", folder_type)
        form.add_field("overwrite", str(overwrite).lower())
        if subfolder:
            form.add_field("subfolder", subfolder)

        result = await self._request("POST", "/upload/image", data=form)
        return UploadResponse(
            name=result.get("name", filename),
            subfolder=result.get("subfolder", subfolder),
            type=result.get("type", folder_type),
        )

    async def upload_mask(
        self,
        mask_data: bytes,
        filename: str,
        original_ref: dict[str, str],
        overwrite: bool = False,
        subfolder: str = "",
    ) -> UploadResponse:
        """Upload a mask file.

        Args:
            mask_data: Raw mask image bytes
            filename: Desired filename
            original_ref: Reference to original image {"filename", "type", "subfolder"}
            overwrite: Whether to overwrite existing file
            subfolder: Subfolder to upload to

        Returns:
            UploadResponse with final name and location
        """
        form = aiohttp.FormData()
        form.add_field("image", mask_data, filename=filename)
        form.add_field("original_ref", json.dumps(original_ref))
        form.add_field("overwrite", str(overwrite).lower())
        if subfolder:
            form.add_field("subfolder", subfolder)

        result = await self._request("POST", "/upload/mask", data=form)
        return UploadResponse(
            name=result.get("name", filename),
            subfolder=result.get("subfolder", subfolder),
            type=result.get("type", "input"),
        )

    # ==================== Model Operations ====================

    async def get_model_folders(self) -> list[str]:
        """Get list of model folder types."""
        result = await self._request("GET", "/models")
        return result if isinstance(result, list) else []

    async def get_models(self, folder: str) -> list[str]:
        """Get list of models in a folder.

        Args:
            folder: Model folder type (e.g., "checkpoints", "loras", "vae")

        Returns:
            List of model filenames
        """
        result = await self._request("GET", f"/models/{folder}")
        return result if isinstance(result, list) else []

    async def get_embeddings(self) -> list[str]:
        """Get list of available embeddings."""
        result = await self._request("GET", "/embeddings")
        return result if isinstance(result, list) else []

    # ==================== Node Info Operations ====================

    async def get_object_info(self, node_class: str | None = None) -> dict[str, Any]:
        """Get node definitions.

        Args:
            node_class: Get info for specific node class, or all if None

        Returns:
            Raw object_info dictionary
        """
        if node_class:
            return await self._request("GET", f"/object_info/{node_class}")
        return await self._request("GET", "/object_info")

    async def get_node_def(self, node_class: str) -> NodeDef:
        """Get parsed node definition for a specific node class.

        Args:
            node_class: The node class type (e.g., "KSampler")

        Returns:
            Parsed NodeDef object
        """
        info = await self.get_object_info(node_class)
        node_info = info.get(node_class, info)
        return self._parse_node_def(node_class, node_info)

    async def get_all_node_defs(self) -> dict[str, NodeDef]:
        """Get all parsed node definitions.

        Returns:
            Dictionary mapping class_type to NodeDef
        """
        info = await self.get_object_info()
        return {
            class_type: self._parse_node_def(class_type, node_info)
            for class_type, node_info in info.items()
        }

    def _parse_node_def(self, class_type: str, info: dict) -> NodeDef:
        """Parse raw object_info into NodeDef."""
        inputs: dict[str, NodeInputSpec] = {}

        input_types = info.get("input", {})
        for category in ["required", "optional"]:
            for name, spec in input_types.get(category, {}).items():
                input_type = spec[0] if isinstance(spec, list) else spec
                options = spec[1] if isinstance(spec, list) and len(spec) > 1 else {}

                inputs[name] = NodeInputSpec(
                    name=name,
                    type=input_type,
                    required=(category == "required"),
                    default=options.get("default"),
                    min=options.get("min"),
                    max=options.get("max"),
                    step=options.get("step"),
                    multiline=options.get("multiline", False),
                    tooltip=options.get("tooltip"),
                )

        output_types = info.get("output", [])
        output_names = info.get("output_name", output_types)
        output_is_list = info.get("output_is_list", [False] * len(output_types))
        output_tooltips = info.get("output_tooltips", [])

        outputs = [
            NodeOutputSpec(
                name=output_names[i] if i < len(output_names) else output_types[i],
                type=output_types[i],
                slot=i,
                is_list=output_is_list[i] if i < len(output_is_list) else False,
                tooltip=output_tooltips[i] if i < len(output_tooltips) else None,
            )
            for i in range(len(output_types))
        ]

        return NodeDef(
            name=class_type,
            display_name=info.get("display_name", class_type),
            category=info.get("category", ""),
            description=info.get("description", ""),
            inputs=inputs,
            outputs=outputs,
            output_node=info.get("output_node", False),
            deprecated=info.get("deprecated", False),
            experimental=info.get("experimental", False),
        )

    # ==================== System Operations ====================

    async def get_system_stats(self) -> SystemStats:
        """Get system statistics."""
        result = await self._request("GET", "/system_stats")
        return SystemStats.from_dict(result)

    async def free_memory(self, unload_models: bool = False, free_memory: bool = True) -> None:
        """Free memory by unloading models and/or clearing caches.

        Args:
            unload_models: Whether to unload all models
            free_memory: Whether to free memory caches
        """
        await self._request(
            "POST",
            "/free",
            json_data={"unload_models": unload_models, "free_memory": free_memory},
        )

    async def get_extensions(self) -> list[str]:
        """Get list of loaded extensions."""
        result = await self._request("GET", "/extensions")
        return result if isinstance(result, list) else []

    # ==================== Utility Methods ====================

    async def is_connected(self) -> bool:
        """Check if ComfyUI server is reachable."""
        try:
            await self.get_system_stats()
            return True
        except (ComfyUIError, aiohttp.ClientError):
            return False

    def get_image_url(
        self,
        filename: str,
        subfolder: str = "",
        folder_type: str = "output",
    ) -> str:
        """Get the full URL for viewing an image.

        Args:
            filename: Name of the image file
            subfolder: Subfolder within the type folder
            folder_type: "output", "input", or "temp"

        Returns:
            Full URL to the image
        """
        params = {"filename": filename, "type": folder_type}
        if subfolder:
            params["subfolder"] = subfolder
        return f"{self.base_url}/view?{urlencode(params)}"
