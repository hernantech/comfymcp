"""MCP tools for programmatic ComfyUI workflow construction.

Provides tools for:
- Listing and searching ComfyUI nodes
- Creating workflow builder sessions
- Adding nodes to workflows with automatic connection handling
- Building and validating workflows
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable
from uuid import uuid4

from mcp.server import Server
from mcp.types import TextContent

from comfymcp.workflow.builder import WorkflowBuilder
from comfymcp.workflow.node_defs import NodeDefCache
from comfymcp.workflow.validation import validate_workflow

if TYPE_CHECKING:
    from comfymcp.client.http import ComfyUIClient

# Global storage for workflow builder sessions
_builder_sessions: dict[str, WorkflowBuilder] = {}

# Global node definition cache
_node_cache: NodeDefCache = NodeDefCache()


def register_builder_tools(
    server: Server, get_client: Callable[[], ComfyUIClient]
) -> None:
    """Register workflow builder tools with the MCP server.

    Args:
        server: The MCP server instance
        get_client: Callable that returns the ComfyUIClient instance
    """

    @server.tool()
    async def list_nodes(
        category: str | None = None,
        search: str | None = None,
    ) -> list[TextContent]:
        """List available ComfyUI nodes with optional filtering.

        Use this tool to discover available nodes for workflow construction.
        You can filter by category or search by name/description.

        Args:
            category: Optional category to filter by (e.g., "loaders", "sampling").
                Use without arguments first to see all categories.
            search: Optional search query to find nodes by name or description.
                Searches are case-insensitive and match partial names.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - nodes: List of node summaries with name, display_name, category
            - count: Number of nodes returned
            - categories: List of all available categories (when no filter applied)
        """
        try:
            # Ensure cache is loaded
            if not _node_cache.is_loaded:
                client = get_client()
                await _node_cache.refresh(client)

            # Get nodes based on filter
            if search:
                nodes = _node_cache.search(search, category=category)
            elif category:
                nodes = _node_cache.list_nodes(category=category)
            else:
                nodes = _node_cache.list_nodes()

            # Build summaries
            node_summaries = [
                {
                    "name": node.name,
                    "display_name": node.display_name,
                    "category": node.category,
                }
                for node in nodes
            ]

            result: dict[str, Any] = {
                "success": True,
                "nodes": node_summaries,
                "count": len(node_summaries),
            }

            # Include categories when no filter is applied
            if not category and not search:
                result["categories"] = _node_cache.list_categories()

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2),
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
    async def get_node_info(class_type: str) -> list[TextContent]:
        """Get detailed information about a specific ComfyUI node.

        Use this tool to understand a node's inputs, outputs, and behavior
        before adding it to a workflow.

        Args:
            class_type: The node class type (e.g., "KSampler", "CheckpointLoaderSimple").
                Use list_nodes to find available node types.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - node: Full node definition with:
                - name: The class type
                - display_name: Human-readable name
                - category: Node category
                - description: What the node does
                - inputs: Dict of input specifications (name, type, required, default, etc.)
                - outputs: List of output specifications (name, type, slot)
                - output_node: Whether this is an output node (like SaveImage)
        """
        try:
            # Ensure cache is loaded
            if not _node_cache.is_loaded:
                client = get_client()
                await _node_cache.refresh(client)

            node_def = _node_cache.get(class_type)

            if node_def is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": False,
                                "error": f"Node type '{class_type}' not found",
                                "error_type": "NodeNotFound",
                            },
                            indent=2,
                        ),
                    )
                ]

            # Serialize node definition
            inputs_data = {}
            for name, spec in node_def.inputs.items():
                inputs_data[name] = {
                    "type": spec.type,
                    "required": spec.required,
                    "default": spec.default,
                }
                if spec.min is not None:
                    inputs_data[name]["min"] = spec.min
                if spec.max is not None:
                    inputs_data[name]["max"] = spec.max
                if spec.step is not None:
                    inputs_data[name]["step"] = spec.step
                if spec.multiline:
                    inputs_data[name]["multiline"] = spec.multiline
                if spec.tooltip:
                    inputs_data[name]["tooltip"] = spec.tooltip

            outputs_data = [
                {
                    "name": output.name,
                    "type": output.type,
                    "slot": output.slot,
                    "is_list": output.is_list,
                }
                for output in node_def.outputs
            ]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "node": {
                                "name": node_def.name,
                                "display_name": node_def.display_name,
                                "category": node_def.category,
                                "description": node_def.description,
                                "inputs": inputs_data,
                                "outputs": outputs_data,
                                "output_node": node_def.output_node,
                                "deprecated": node_def.deprecated,
                                "experimental": node_def.experimental,
                            },
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
    async def refresh_nodes() -> list[TextContent]:
        """Refresh the node definition cache from the ComfyUI server.

        Call this tool to reload available nodes after installing new
        custom nodes or when the cache may be stale.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - count: Number of node definitions loaded
            - categories: Number of unique categories
        """
        try:
            client = get_client()
            await _node_cache.refresh(client)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "count": len(_node_cache._cache),
                            "categories": len(_node_cache._categories),
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
    async def create_workflow() -> list[TextContent]:
        """Create a new workflow builder session.

        Creates an empty workflow that you can add nodes to using add_node.
        The session ID returned must be used for all subsequent operations
        on this workflow.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - session_id: Unique identifier for this workflow session
            - message: Description of what to do next
        """
        try:
            # Ensure cache is loaded for validation
            if not _node_cache.is_loaded:
                client = get_client()
                await _node_cache.refresh(client)

            session_id = str(uuid4())
            builder = WorkflowBuilder(cache=_node_cache)
            _builder_sessions[session_id] = builder

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "session_id": session_id,
                            "message": "Workflow session created. Use add_node to add nodes.",
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
    async def add_node(
        session_id: str,
        class_type: str,
        inputs: dict[str, Any] | None = None,
    ) -> list[TextContent]:
        """Add a node to a workflow builder session.

        Adds a node of the specified type to the workflow. Returns the node's
        ID and output connections that can be used as inputs to other nodes.

        Args:
            session_id: The workflow session ID from create_workflow
            class_type: The node type to add (e.g., "KSampler", "CheckpointLoaderSimple")
            inputs: Optional dict of input values. For connections from other nodes,
                use the format [node_id, slot] (e.g., ["1", 0] for first output of node 1)

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - node_id: The ID assigned to this node
            - outputs: Dict mapping output names to [node_id, slot] connections
                that can be used as inputs to other nodes

        Example:
            # First add a checkpoint loader
            add_node(session_id, "CheckpointLoaderSimple",
                inputs={"ckpt_name": "v1-5-pruned.safetensors"})
            # Returns: {node_id: "1", outputs: {MODEL: ["1", 0], CLIP: ["1", 1], VAE: ["1", 2]}}

            # Then use its outputs in another node
            add_node(session_id, "KSampler",
                inputs={"model": ["1", 0], "seed": 42, ...})
        """
        try:
            # Validate session
            if session_id not in _builder_sessions:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": False,
                                "error": f"Session '{session_id}' not found",
                                "error_type": "SessionNotFound",
                            },
                            indent=2,
                        ),
                    )
                ]

            builder = _builder_sessions[session_id]
            node_inputs = inputs or {}

            # Add the node
            node_ref = builder.add_node(class_type, **node_inputs)

            # Build outputs dict
            outputs = {}
            if node_ref.node_def:
                for output in node_ref.node_def.outputs:
                    outputs[output.name] = [node_ref.node_id, output.slot]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "node_id": node_ref.node_id,
                            "outputs": outputs,
                        },
                        indent=2,
                    ),
                )
            ]
        except ValueError as e:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": False,
                            "error": str(e),
                            "error_type": "ValidationError",
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
    async def build_workflow(session_id: str) -> list[TextContent]:
        """Build and validate a workflow from a builder session.

        Converts the workflow builder session into a ComfyUI API format
        workflow dict and validates it for correctness.

        Args:
            session_id: The workflow session ID from create_workflow

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - workflow: The complete workflow in ComfyUI API format
            - valid: Boolean indicating if validation passed
            - errors: List of validation errors (if any)
            - warnings: List of validation warnings (if any)
            - node_count: Number of nodes in the workflow
        """
        try:
            # Validate session
            if session_id not in _builder_sessions:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "success": False,
                                "error": f"Session '{session_id}' not found",
                                "error_type": "SessionNotFound",
                            },
                            indent=2,
                        ),
                    )
                ]

            builder = _builder_sessions[session_id]

            # Build the workflow
            workflow = builder.build()

            # Validate
            validation_result = builder.validate()

            # Serialize errors and warnings
            errors = [
                {
                    "node_id": e.node_id,
                    "input_name": e.input_name,
                    "error_type": e.error_type,
                    "message": e.message,
                }
                for e in validation_result.errors
            ]

            warnings = [
                {
                    "node_id": w.node_id,
                    "input_name": w.input_name,
                    "error_type": w.error_type,
                    "message": w.message,
                }
                for w in validation_result.warnings
            ]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "workflow": workflow,
                            "valid": validation_result.valid,
                            "errors": errors,
                            "warnings": warnings,
                            "node_count": len(workflow),
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
    async def validate_workflow(workflow: dict[str, Any]) -> list[TextContent]:
        """Validate a raw workflow dictionary.

        Use this to validate workflows that were not created through the
        builder tools, such as workflows loaded from files or received
        from other sources.

        Args:
            workflow: The workflow in ComfyUI API format, a dictionary mapping
                node_id to node configuration with class_type and inputs.

        Returns:
            JSON object containing:
            - success: Boolean indicating if the operation succeeded
            - valid: Boolean indicating if the workflow is valid
            - errors: List of validation errors with:
                - node_id: The node that has the error
                - input_name: The specific input (if applicable)
                - error_type: Type of error (e.g., "missing_required_input")
                - message: Human-readable error description
            - warnings: List of validation warnings (same format as errors)
        """
        try:
            # Ensure cache is loaded for validation
            if not _node_cache.is_loaded:
                client = get_client()
                await _node_cache.refresh(client)

            # Validate the workflow
            result = validate_workflow(workflow, cache=_node_cache)

            # Serialize errors and warnings
            errors = [
                {
                    "node_id": e.node_id,
                    "input_name": e.input_name,
                    "error_type": e.error_type,
                    "message": e.message,
                }
                for e in result.errors
            ]

            warnings = [
                {
                    "node_id": w.node_id,
                    "input_name": w.input_name,
                    "error_type": w.error_type,
                    "message": w.message,
                }
                for w in result.warnings
            ]

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "valid": result.valid,
                            "errors": errors,
                            "warnings": warnings,
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
