"""Base class for workflow templates.

Provides a common interface for building ComfyUI workflows from
configurable parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from comfymcp.workflow import NodeDefCache


@dataclass
class WorkflowTemplate:
    """Base class for workflow templates.

    Subclasses should define their parameters as dataclass fields
    and implement the build() method to construct the workflow.

    Example:
        @dataclass
        class MyTemplate(WorkflowTemplate):
            prompt: str
            width: int = 512
            height: int = 512

            def build(self, cache=None):
                builder = WorkflowBuilder(cache)
                # ... construct workflow ...
                return builder.build()
    """

    def build(self, cache: NodeDefCache | None = None) -> dict[str, Any]:
        """Build the workflow.

        Args:
            cache: Optional NodeDefCache for validation and output lookups.
                   Without a cache, NodeRefs won't have output information.

        Returns:
            A workflow dict in ComfyUI API format.

        Raises:
            NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclasses must implement build()")

    def validate_params(self) -> list[str]:
        """Validate template parameters.

        Override this method to add parameter validation logic.

        Returns:
            A list of error messages. Empty list means validation passed.
        """
        return []
