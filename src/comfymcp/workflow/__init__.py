"""Workflow building utilities for ComfyUI."""

from comfymcp.workflow.builder import WorkflowBuilder, build_workflow
from comfymcp.workflow.node_ref import NodeRef, is_node_ref, is_connection
from comfymcp.workflow.node_defs import NodeDefCache, NodeDef, OutputSpec, InputSpec
from comfymcp.workflow.validation import (
    WorkflowValidator,
    ValidationResult,
    ValidationError,
    validate_workflow,
)

__all__ = [
    # Builder
    "WorkflowBuilder",
    "build_workflow",
    # NodeRef
    "NodeRef",
    "is_node_ref",
    "is_connection",
    # Node definitions
    "NodeDefCache",
    "NodeDef",
    "OutputSpec",
    "InputSpec",
    # Validation
    "WorkflowValidator",
    "ValidationResult",
    "ValidationError",
    "validate_workflow",
]
