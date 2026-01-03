"""Node definition cache for ComfyUI workflow building.

This module provides a cache for ComfyUI node definitions, enabling
efficient lookup and search of nodes, as well as type validation
for node connections.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from comfymcp.client import ComfyUIClient

from comfymcp.client.types import NodeDef, NodeInputSpec, NodeOutputSpec

logger = logging.getLogger(__name__)

# Re-export for backwards compatibility with workflow/__init__.py
# These aliases allow importing from workflow module directly
OutputSpec = NodeOutputSpec
InputSpec = NodeInputSpec
# NodeDef is also re-exported (imported above from client.types)
__all__ = [
    "NodeDefCache",
    "NodeDef",
    "OutputSpec",
    "InputSpec",
    "NodeInputSpec",
    "NodeOutputSpec",
]


class NodeDefCache:
    """Cache for ComfyUI node definitions.

    Provides efficient lookup, search, and validation of node definitions
    fetched from the ComfyUI server's /object_info endpoint.

    Example:
        cache = NodeDefCache()
        async with ComfyUIClient() as client:
            await cache.refresh(client)

        # Get a specific node
        ksampler = cache.get("KSampler")

        # Search for nodes
        samplers = cache.search("sampler", category="sampling")

        # Validate a connection
        if cache.validate_connection("MODEL", "MODEL"):
            print("Connection is valid")
    """

    def __init__(self) -> None:
        """Initialize an empty node definition cache."""
        self._cache: dict[str, NodeDef] = {}
        self._categories: set[str] = set()

    @property
    def is_loaded(self) -> bool:
        """Check if the cache has been populated with node definitions."""
        return len(self._cache) > 0

    async def refresh(self, client: ComfyUIClient) -> None:
        """Refresh the cache from the ComfyUI server.

        Fetches all node definitions from the server's /object_info
        endpoint and populates the cache.

        Args:
            client: Connected ComfyUIClient instance
        """
        logger.debug("Refreshing node definition cache from server")
        node_defs = await client.get_all_node_defs()

        self._cache = node_defs
        self._categories = {
            node_def.category
            for node_def in node_defs.values()
            if node_def.category
        }

        logger.info(
            "Loaded %d node definitions in %d categories",
            len(self._cache),
            len(self._categories),
        )

    def get(self, class_type: str) -> NodeDef | None:
        """Get a node definition by its class type.

        Args:
            class_type: The node class type (e.g., "KSampler", "CheckpointLoaderSimple")

        Returns:
            The NodeDef if found, None otherwise
        """
        return self._cache.get(class_type)

    def search(
        self,
        query: str,
        category: str | None = None,
    ) -> list[NodeDef]:
        """Search for nodes by name or description.

        Performs case-insensitive matching against the node's name,
        display name, and description fields.

        Args:
            query: Search query string
            category: Optional category to filter by

        Returns:
            List of matching NodeDef objects, sorted by relevance
        """
        query_lower = query.lower()
        results: list[tuple[int, NodeDef]] = []

        for node_def in self._cache.values():
            # Skip if category filter doesn't match
            if category is not None and node_def.category != category:
                continue

            # Calculate relevance score
            score = 0
            name_lower = node_def.name.lower()
            display_lower = (node_def.display_name or "").lower()
            desc_lower = (node_def.description or "").lower()

            # Exact match on name is highest priority
            if name_lower == query_lower:
                score = 100
            elif display_lower == query_lower:
                score = 95
            # Name starts with query
            elif name_lower.startswith(query_lower):
                score = 80
            elif display_lower.startswith(query_lower):
                score = 75
            # Name contains query
            elif query_lower in name_lower:
                score = 60
            elif query_lower in display_lower:
                score = 55
            # Description contains query
            elif query_lower in desc_lower:
                score = 30

            if score > 0:
                results.append((score, node_def))

        # Sort by score descending, then by name
        results.sort(key=lambda x: (-x[0], x[1].name))
        return [node_def for _, node_def in results]

    def list_categories(self) -> list[str]:
        """List all available node categories.

        Returns:
            Sorted list of category names
        """
        return sorted(self._categories)

    def list_nodes(self, category: str | None = None) -> list[NodeDef]:
        """List all nodes, optionally filtered by category.

        Args:
            category: Optional category to filter by

        Returns:
            List of NodeDef objects, sorted by name
        """
        if category is None:
            nodes = list(self._cache.values())
        else:
            nodes = [
                node_def
                for node_def in self._cache.values()
                if node_def.category == category
            ]

        return sorted(nodes, key=lambda n: n.name)

    def get_inputs(self, class_type: str) -> dict[str, NodeInputSpec]:
        """Get the input specifications for a node.

        Args:
            class_type: The node class type

        Returns:
            Dictionary mapping input names to their specifications

        Raises:
            KeyError: If the node class type is not found
        """
        node_def = self._cache.get(class_type)
        if node_def is None:
            raise KeyError(f"Node type '{class_type}' not found in cache")
        return node_def.inputs

    def get_outputs(self, class_type: str) -> list[NodeOutputSpec]:
        """Get the output specifications for a node.

        Args:
            class_type: The node class type

        Returns:
            List of output specifications

        Raises:
            KeyError: If the node class type is not found
        """
        node_def = self._cache.get(class_type)
        if node_def is None:
            raise KeyError(f"Node type '{class_type}' not found in cache")
        return node_def.outputs

    def get_output_slot(self, class_type: str, output_name: str) -> int:
        """Get the slot index for a named output.

        Args:
            class_type: The node class type
            output_name: The name of the output

        Returns:
            The slot index (0-based)

        Raises:
            KeyError: If the node class type is not found
            ValueError: If the output name is not found
        """
        node_def = self._cache.get(class_type)
        if node_def is None:
            raise KeyError(f"Node type '{class_type}' not found in cache")
        return node_def.get_output_slot(output_name)

    def validate_connection(self, from_type: str, to_type: str) -> bool:
        """Check if two types are compatible for connection.

        ComfyUI type matching rules:
        - Exact match: "MODEL" connects to "MODEL"
        - Wildcard: "*" matches anything
        - Union types: "STRING,INT" matches if either side is a subset of the other

        Args:
            from_type: The output type (source)
            to_type: The input type (destination)

        Returns:
            True if the types are compatible, False otherwise
        """
        return _types_compatible(from_type, to_type)


def _types_compatible(from_type: str, to_type: str) -> bool:
    """Check if two ComfyUI types are compatible.

    Implements ComfyUI's type matching logic from comfy.comfy_types.node_typing.

    Rules:
    1. Wildcard "*" matches anything
    2. Exact string match
    3. Union types (comma-separated): compatible if either is a subset of the other

    Args:
        from_type: The output type (source)
        to_type: The input type (destination)

    Returns:
        True if compatible, False otherwise
    """
    # Wildcard matches everything
    if from_type == "*" or to_type == "*":
        return True

    # Exact match
    if from_type == to_type:
        return True

    # Handle union types (comma-separated)
    from_set = frozenset(from_type.split(","))
    to_set = frozenset(to_type.split(","))

    # Compatible if either is a subset of the other
    return to_set.issubset(from_set) or from_set.issubset(to_set)
