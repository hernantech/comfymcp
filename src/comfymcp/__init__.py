"""ComfyMCP - MCP server for ComfyUI workflow automation."""

__version__ = "0.1.0"

from comfymcp.client import ComfyUIClient, ComfyUIWebSocket
from comfymcp.workflow import WorkflowBuilder, NodeRef, NodeDefCache
from comfymcp.server import create_server, main

__all__ = [
    # Server
    "create_server",
    "main",
    # Client
    "ComfyUIClient",
    "ComfyUIWebSocket",
    # Workflow
    "WorkflowBuilder",
    "NodeRef",
    "NodeDefCache",
    # Version
    "__version__",
]
