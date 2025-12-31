"""MCP resources for ComfyUI node definitions."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable
from urllib.parse import unquote

from mcp.server import Server
from mcp.types import Resource, TextResourceContents

if TYPE_CHECKING:
    from comfymcp.workflow.node_defs import NodeDefCache


def register_node_resources(
    server: Server,
    get_cache: Callable[[], NodeDefCache],
) -> None:
    """Register node definition resources with the MCP server.

    Provides resources for browsing available ComfyUI nodes:
    - comfyui://nodes - List all nodes (summary)
    - comfyui://nodes/categories - List all categories
    - comfyui://nodes/category/{name} - Nodes in a category
    - comfyui://nodes/{class_type} - Specific node definition

    Args:
        server: The MCP server instance
        get_cache: Callable that returns the NodeDefCache instance
    """

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available node resources."""
        resources = [
            Resource(
                uri="comfyui://nodes",
                name="All ComfyUI Nodes",
                description="List of all available ComfyUI nodes with summaries",
                mimeType="application/json",
            ),
            Resource(
                uri="comfyui://nodes/categories",
                name="Node Categories",
                description="List of all node categories",
                mimeType="application/json",
            ),
        ]

        # Add category resources if cache is loaded
        cache = get_cache()
        if cache.is_loaded:
            for category in cache.list_categories():
                resources.append(
                    Resource(
                        uri=f"comfyui://nodes/category/{category}",
                        name=f"Category: {category}",
                        description=f"Nodes in the '{category}' category",
                        mimeType="application/json",
                    )
                )

        return resources

    @server.read_resource()
    async def read_resource(uri: str) -> TextResourceContents:
        """Read a node resource by URI."""
        cache = get_cache()

        if not cache.is_loaded:
            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({
                    "error": "Node cache not loaded. Use refresh_nodes tool first.",
                }, indent=2),
            )

        # Parse the URI
        if uri == "comfyui://nodes":
            return _list_all_nodes(uri, cache)
        elif uri == "comfyui://nodes/categories":
            return _list_categories(uri, cache)
        elif uri.startswith("comfyui://nodes/category/"):
            category = unquote(uri.replace("comfyui://nodes/category/", ""))
            return _list_nodes_in_category(uri, cache, category)
        elif uri.startswith("comfyui://nodes/"):
            class_type = unquote(uri.replace("comfyui://nodes/", ""))
            return _get_node_definition(uri, cache, class_type)
        else:
            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({"error": f"Unknown resource: {uri}"}, indent=2),
            )


def _list_all_nodes(uri: str, cache: NodeDefCache) -> TextResourceContents:
    """List all nodes with summaries."""
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

    return TextResourceContents(
        uri=uri,
        mimeType="application/json",
        text=json.dumps({
            "count": len(summaries),
            "nodes": summaries,
        }, indent=2),
    )


def _list_categories(uri: str, cache: NodeDefCache) -> TextResourceContents:
    """List all node categories."""
    categories = cache.list_categories()

    # Count nodes per category
    category_counts = {}
    for node in cache.list_nodes():
        cat = node.category or "uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return TextResourceContents(
        uri=uri,
        mimeType="application/json",
        text=json.dumps({
            "count": len(categories),
            "categories": [
                {"name": cat, "node_count": category_counts.get(cat, 0)}
                for cat in categories
            ],
        }, indent=2),
    )


def _list_nodes_in_category(uri: str, cache: NodeDefCache, category: str) -> TextResourceContents:
    """List nodes in a specific category."""
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

    return TextResourceContents(
        uri=uri,
        mimeType="application/json",
        text=json.dumps({
            "category": category,
            "count": len(summaries),
            "nodes": summaries,
        }, indent=2),
    )


def _get_node_definition(uri: str, cache: NodeDefCache, class_type: str) -> TextResourceContents:
    """Get a specific node definition."""
    node = cache.get(class_type)

    if node is None:
        return TextResourceContents(
            uri=uri,
            mimeType="application/json",
            text=json.dumps({
                "error": f"Node not found: {class_type}",
            }, indent=2),
        )

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

    return TextResourceContents(
        uri=uri,
        mimeType="application/json",
        text=json.dumps({
            "name": node.name,
            "display_name": node.display_name,
            "category": node.category,
            "description": node.description,
            "output_node": node.output_node,
            "deprecated": node.deprecated,
            "experimental": node.experimental,
            "inputs": inputs,
            "outputs": outputs,
        }, indent=2),
    )
