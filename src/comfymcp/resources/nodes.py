"""MCP resources for ComfyUI node definitions."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable

from mcp.server.fastmcp import FastMCP

if TYPE_CHECKING:
    from comfymcp.workflow.node_defs import NodeDefCache


def register_node_resources(
    server: FastMCP,
    get_cache: Callable[[], NodeDefCache],
) -> None:
    """Register node definition resources with the MCP server.

    Provides resources for browsing available ComfyUI nodes:
    - comfyui://nodes - List all nodes (summary)
    - comfyui://nodes/categories - List all categories
    - comfyui://nodes/category/{name} - Nodes in a category
    - comfyui://nodes/{class_type} - Specific node definition

    Args:
        server: The FastMCP server instance
        get_cache: Callable that returns the NodeDefCache instance
    """

    @server.resource("comfyui://nodes", name="All ComfyUI Nodes", mime_type="application/json")
    def list_all_nodes() -> str:
        """List of all available ComfyUI nodes with summaries."""
        cache = get_cache()

        if not cache.is_loaded:
            return json.dumps({
                "error": "Node cache not loaded. Use refresh_nodes tool first.",
            }, indent=2)

        nodes = cache.list_nodes()
        summaries = [
            {
                "name": node.name,
                "display_name": node.display_name,
                "category": node.category,
                "description": node.description[:100] + "..." if len(node.description) > 100 else node.description,
                "output_node": node.output_node,
                "input_count": len(node.inputs),
                "output_count": len(node.outputs),
            }
            for node in nodes
        ]

        return json.dumps({
            "count": len(summaries),
            "nodes": summaries,
        }, indent=2)

    @server.resource("comfyui://nodes/categories", name="Node Categories", mime_type="application/json")
    def list_categories() -> str:
        """List of all node categories."""
        cache = get_cache()

        if not cache.is_loaded:
            return json.dumps({
                "error": "Node cache not loaded. Use refresh_nodes tool first.",
            }, indent=2)

        categories = cache.list_categories()

        # Count nodes per category
        category_counts = {}
        for node in cache.list_nodes():
            cat = node.category or "uncategorized"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return json.dumps({
            "count": len(categories),
            "categories": [
                {"name": cat, "node_count": category_counts.get(cat, 0)}
                for cat in categories
            ],
        }, indent=2)

    @server.resource("comfyui://nodes/category/{category}", name="Nodes by Category", mime_type="application/json")
    def list_nodes_in_category(category: str) -> str:
        """List nodes in a specific category."""
        cache = get_cache()

        if not cache.is_loaded:
            return json.dumps({
                "error": "Node cache not loaded. Use refresh_nodes tool first.",
            }, indent=2)

        nodes = cache.list_nodes(category=category)

        summaries = [
            {
                "name": node.name,
                "display_name": node.display_name,
                "description": node.description[:100] + "..." if len(node.description) > 100 else node.description,
                "output_node": node.output_node,
            }
            for node in nodes
        ]

        return json.dumps({
            "category": category,
            "count": len(summaries),
            "nodes": summaries,
        }, indent=2)

    @server.resource("comfyui://nodes/{class_type}", name="Node Definition", mime_type="application/json")
    def get_node_definition(class_type: str) -> str:
        """Get a specific node definition."""
        cache = get_cache()

        if not cache.is_loaded:
            return json.dumps({
                "error": "Node cache not loaded. Use refresh_nodes tool first.",
            }, indent=2)

        node = cache.get(class_type)

        if node is None:
            return json.dumps({
                "error": f"Node not found: {class_type}",
            }, indent=2)

        # Format inputs
        inputs = {}
        for name, spec in node.inputs.items():
            input_info = {
                "type": spec.type if isinstance(spec.type, str) else list(spec.type),
                "required": spec.required,
            }
            if spec.default is not None:
                input_info["default"] = spec.default
            if spec.min is not None:
                input_info["min"] = spec.min
            if spec.max is not None:
                input_info["max"] = spec.max
            if spec.tooltip:
                input_info["tooltip"] = spec.tooltip
            inputs[name] = input_info

        # Format outputs
        outputs = [
            {
                "name": out.name,
                "type": out.type,
                "slot": out.slot,
                "is_list": out.is_list,
            }
            for out in node.outputs
        ]

        return json.dumps({
            "name": node.name,
            "display_name": node.display_name,
            "category": node.category,
            "description": node.description,
            "output_node": node.output_node,
            "deprecated": node.deprecated,
            "experimental": node.experimental,
            "inputs": inputs,
            "outputs": outputs,
        }, indent=2)
