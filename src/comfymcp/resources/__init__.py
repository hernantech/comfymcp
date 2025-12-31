"""MCP resources for ComfyUI data."""

from comfymcp.resources.nodes import register_node_resources
from comfymcp.resources.outputs import register_output_resources

__all__ = [
    "register_node_resources",
    "register_output_resources",
]
