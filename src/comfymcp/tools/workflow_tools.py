"""MCP tools for ComfyUI workflow queue and history management."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

if TYPE_CHECKING:
    from comfymcp.client.http import ComfyUIClient


def register_workflow_tools(server: FastMCP, get_client: Callable[[], ComfyUIClient]) -> None:
    """Register workflow management tools with the MCP server.

    Args:
        server: The MCP server instance
        get_client: Callable that returns the ComfyUIClient instance
    """

    @server.tool()
    async def queue_prompt(
        workflow: dict[str, Any],
        client_id: str | None = None,
    ) -> list[TextContent]:
        """Queue a ComfyUI workflow for execution.

        Submits a workflow to the ComfyUI execution queue and returns a prompt ID
        that can be used to track the execution status.

        Args:
            workflow: The workflow in ComfyUI API format, a dictionary mapping
                node_id to node configuration with class_type and inputs.
            client_id: Optional client ID for WebSocket correlation. If provided,
                execution progress can be tracked via WebSocket.

        Returns:
            JSON object containing:
            - prompt_id: Unique identifier for tracking this execution
            - number: Queue position number
            - node_errors: Dict of any validation errors found in nodes
        """
        client = get_client()
        try:
            result = await client.queue_prompt(workflow, client_id=client_id)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "prompt_id": result.prompt_id,
                            "number": result.number,
                            "node_errors": result.node_errors,
                        },
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        indent=2,
                    ),
                )
            ]

    @server.tool()
    async def get_queue_status() -> list[TextContent]:
        """Get the current state of the ComfyUI execution queue.

        Returns information about currently running and pending workflow executions.

        Returns:
            JSON object containing:
            - running: List of currently executing jobs with their prompt_id and number
            - pending: List of jobs waiting in the queue with their prompt_id and number
            - queue_length: Total number of jobs (running + pending)
        """
        client = get_client()
        try:
            queue = await client.get_queue()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "running": [
                                {
                                    "prompt_id": item.prompt_id,
                                    "number": item.number,
                                }
                                for item in queue.running
                            ],
                            "pending": [
                                {
                                    "prompt_id": item.prompt_id,
                                    "number": item.number,
                                }
                                for item in queue.pending
                            ],
                            "queue_length": queue.queue_remaining,
                        },
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        indent=2,
                    ),
                )
            ]

    @server.tool()
    async def clear_queue() -> list[TextContent]:
        """Clear all pending items from the ComfyUI execution queue.

        Removes all queued workflows that have not yet started executing.
        Currently running workflows are not affected.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - message: Description of the result
        """
        client = get_client()
        try:
            await client.clear_queue()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "message": "Queue cleared successfully",
                        },
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        indent=2,
                    ),
                )
            ]

    @server.tool()
    async def delete_queue_item(prompt_id: str) -> list[TextContent]:
        """Remove a specific item from the ComfyUI execution queue.

        Deletes a queued workflow by its prompt ID. If the workflow is currently
        executing, use interrupt_execution instead.

        Args:
            prompt_id: The unique identifier of the prompt to remove from the queue.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - message: Description of the result
            - prompt_id: The ID of the deleted item
        """
        client = get_client()
        try:
            await client.delete_queue_item(prompt_id)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "message": f"Queue item {prompt_id} deleted successfully",
                            "prompt_id": prompt_id,
                        },
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "prompt_id": prompt_id,
                        },
                        indent=2,
                    ),
                )
            ]

    @server.tool()
    async def interrupt_execution() -> list[TextContent]:
        """Interrupt the currently executing workflow in ComfyUI.

        Stops the workflow that is currently being processed. This is useful
        for canceling long-running generations.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - message: Description of the result
        """
        client = get_client()
        try:
            await client.interrupt()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "message": "Execution interrupted successfully",
                        },
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        indent=2,
                    ),
                )
            ]

    @server.tool()
    async def get_history(
        prompt_id: str | None = None,
        max_items: int | None = None,
    ) -> list[TextContent]:
        """Get execution history from ComfyUI.

        Retrieves the history of executed workflows, including their outputs.
        Can fetch all history, a limited number of recent items, or a specific
        execution by prompt ID.

        Args:
            prompt_id: Optional. If provided, returns only the history for this
                specific prompt. Otherwise returns multiple history entries.
            max_items: Optional. Maximum number of history entries to return.
                Only applies when prompt_id is not specified.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - history: Dict mapping prompt_id to history entry with:
                - prompt_id: The unique identifier
                - outputs: Dict of node outputs (images, etc.)
                - status: Execution status information
        """
        client = get_client()
        try:
            history = await client.get_history(prompt_id=prompt_id, max_items=max_items)
            history_data = {}
            for pid, entry in history.items():
                history_data[pid] = {
                    "prompt_id": entry.prompt_id,
                    "outputs": entry.outputs,
                    "status": entry.status,
                }
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "history": history_data,
                            "count": len(history_data),
                        },
                        indent=2,
                    ),
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        indent=2,
                    ),
                )
            ]

    @server.tool()
    async def get_job_status(prompt_id: str) -> list[TextContent]:
        """Get the status of a specific ComfyUI job.

        Checks the current state of a workflow execution, including whether it's
        queued, running, completed, or failed. For completed jobs, includes the
        output information.

        Args:
            prompt_id: The unique identifier of the prompt to check.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the lookup succeeded
            - prompt_id: The queried prompt ID
            - status: One of "running", "pending", "completed", or "not_found"
            - outputs: If completed, the output data from the execution
            - queue_position: If pending, the position in the queue
        """
        client = get_client()
        try:
            # First check if it's in the queue
            queue = await client.get_queue()

            # Check running jobs
            for item in queue.running:
                if item.prompt_id == prompt_id:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "success": True,
                                    "prompt_id": prompt_id,
                                    "status": "running",
                                    "queue_number": item.number,
                                },
                                indent=2,
                            ),
                        )
                    ]

            # Check pending jobs
            for idx, item in enumerate(queue.pending):
                if item.prompt_id == prompt_id:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "success": True,
                                    "prompt_id": prompt_id,
                                    "status": "pending",
                                    "queue_position": idx + 1,
                                    "queue_number": item.number,
                                },
                                indent=2,
                            ),
                        )
                    ]

            # Not in queue, check history
            history = await client.get_history(prompt_id=prompt_id)

            if prompt_id in history:
                entry = history[prompt_id]
                status_info = entry.status or {}
                # Determine completion status from status_info
                completed = status_info.get("completed", False) if status_info else True
                status_text = "completed" if completed else "error"

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": True,
                                "prompt_id": prompt_id,
                                "status": status_text,
                                "outputs": entry.outputs,
                                "status_info": status_info,
                            },
                            indent=2,
                        ),
                    )
                ]

            # Not found anywhere
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "prompt_id": prompt_id,
                            "status": "not_found",
                            "message": "Prompt ID not found in queue or history",
                        },
                        indent=2,
                    ),
                )
            ]

        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "prompt_id": prompt_id,
                        },
                        indent=2,
                    ),
                )
            ]
