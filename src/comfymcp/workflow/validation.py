"""Validation utilities for workflow construction.

Provides type checking, input validation, and connection validation
to catch errors early before submitting workflows to ComfyUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from comfymcp.client.types import NodeDef, NodeInputSpec
    from comfymcp.workflow.node_defs import NodeDefCache


@dataclass
class ValidationError:
    """A single validation error."""

    node_id: str
    input_name: str | None
    error_type: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        if self.input_name:
            return f"[{self.node_id}].{self.input_name}: {self.message}"
        return f"[{self.node_id}]: {self.message}"


@dataclass
class ValidationResult:
    """Result of workflow validation."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid

    def __str__(self) -> str:
        if self.valid:
            if self.warnings:
                return f"Valid with {len(self.warnings)} warning(s)"
            return "Valid"
        return f"Invalid: {len(self.errors)} error(s)"

    def add_error(
        self,
        node_id: str,
        error_type: str,
        message: str,
        input_name: str | None = None,
        **details: Any,
    ) -> None:
        """Add an error to the validation result."""
        self.errors.append(
            ValidationError(
                node_id=node_id,
                input_name=input_name,
                error_type=error_type,
                message=message,
                details=details,
            )
        )
        self.valid = False

    def add_warning(
        self,
        node_id: str,
        error_type: str,
        message: str,
        input_name: str | None = None,
        **details: Any,
    ) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(
            ValidationError(
                node_id=node_id,
                input_name=input_name,
                error_type=error_type,
                message=message,
                details=details,
            )
        )


class WorkflowValidator:
    """Validates ComfyUI workflows before submission.

    Performs several checks:
    - Node class types exist
    - Required inputs are provided
    - Input values match expected types
    - Connections reference valid nodes and outputs
    - Connection types are compatible

    Example:
        validator = WorkflowValidator(node_cache)
        result = validator.validate(workflow)

        if not result.valid:
            for error in result.errors:
                print(f"Error: {error}")
    """

    def __init__(self, cache: NodeDefCache | None = None) -> None:
        """Initialize the validator.

        Args:
            cache: Optional node definition cache for type checking.
                   If not provided, only structural validation is performed.
        """
        self.cache = cache

    def validate(self, workflow: dict[str, Any]) -> ValidationResult:
        """Validate a workflow.

        Args:
            workflow: The workflow in API format (node_id -> {class_type, inputs})

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        if not workflow:
            result.add_error("", "empty_workflow", "Workflow is empty")
            return result

        # Track output nodes for later check
        has_output_node = False

        for node_id, node_config in workflow.items():
            # Check node structure
            if not isinstance(node_config, dict):
                result.add_error(
                    node_id,
                    "invalid_node",
                    f"Node config must be a dict, got {type(node_config).__name__}",
                )
                continue

            if "class_type" not in node_config:
                result.add_error(
                    node_id,
                    "missing_class_type",
                    "Node is missing 'class_type' field",
                )
                continue

            class_type = node_config["class_type"]
            inputs = node_config.get("inputs", {})

            # Validate against node definition if cache is available
            if self.cache and self.cache.is_loaded:
                node_def = self.cache.get(class_type)

                if node_def is None:
                    result.add_error(
                        node_id,
                        "unknown_node_type",
                        f"Unknown node type: {class_type}",
                    )
                    continue

                if node_def.output_node:
                    has_output_node = True

                # Validate inputs
                self._validate_inputs(result, node_id, node_def, inputs, workflow)

        # Check for output nodes
        if self.cache and self.cache.is_loaded and not has_output_node:
            result.add_warning(
                "",
                "no_output_node",
                "Workflow has no output nodes (like SaveImage). "
                "It may not produce any results.",
            )

        return result

    def _validate_inputs(
        self,
        result: ValidationResult,
        node_id: str,
        node_def: NodeDef,
        inputs: dict[str, Any],
        workflow: dict[str, Any],
    ) -> None:
        """Validate the inputs for a single node."""

        # Check for missing required inputs
        for input_name, input_spec in node_def.inputs.items():
            if input_spec.required and input_name not in inputs:
                # Check if it has a default value
                if input_spec.default is None:
                    result.add_error(
                        node_id,
                        "missing_required_input",
                        f"Missing required input: {input_name}",
                        input_name=input_name,
                    )

        # Validate each provided input
        for input_name, input_value in inputs.items():
            input_spec = node_def.inputs.get(input_name)

            if input_spec is None:
                # Unknown input - could be a hidden input or extension
                result.add_warning(
                    node_id,
                    "unknown_input",
                    f"Unknown input: {input_name}",
                    input_name=input_name,
                )
                continue

            # Check if it's a connection
            if self._is_connection(input_value):
                self._validate_connection(
                    result, node_id, input_name, input_spec, input_value, workflow
                )
            else:
                # Validate the value
                self._validate_value(result, node_id, input_name, input_spec, input_value)

    def _validate_connection(
        self,
        result: ValidationResult,
        node_id: str,
        input_name: str,
        input_spec: NodeInputSpec,
        connection: list,
        workflow: dict[str, Any],
    ) -> None:
        """Validate a connection to another node."""
        from_node_id, from_slot = connection[0], connection[1]

        # Check if source node exists
        if from_node_id not in workflow:
            result.add_error(
                node_id,
                "invalid_connection",
                f"Connection references non-existent node: {from_node_id}",
                input_name=input_name,
                source_node=from_node_id,
                source_slot=from_slot,
            )
            return

        # Validate types if cache is available
        if self.cache and self.cache.is_loaded:
            from_node_config = workflow[from_node_id]
            from_class_type = from_node_config.get("class_type")
            from_node_def = self.cache.get(from_class_type)

            if from_node_def is not None:
                # Check if slot is valid
                if from_slot >= len(from_node_def.outputs):
                    result.add_error(
                        node_id,
                        "invalid_slot",
                        f"Node {from_node_id} ({from_class_type}) has no output slot {from_slot}",
                        input_name=input_name,
                        source_node=from_node_id,
                        source_slot=from_slot,
                        available_slots=len(from_node_def.outputs),
                    )
                    return

                # Check type compatibility
                from_output = from_node_def.outputs[from_slot]
                from_type = from_output.type
                to_type = input_spec.type

                # Skip type check for combo/list types (those are value lists)
                if not isinstance(to_type, list):
                    if not self.cache.validate_connection(from_type, to_type):
                        result.add_error(
                            node_id,
                            "type_mismatch",
                            f"Type mismatch: {from_type} -> {to_type}",
                            input_name=input_name,
                            source_type=from_type,
                            expected_type=to_type,
                        )

    def _validate_value(
        self,
        result: ValidationResult,
        node_id: str,
        input_name: str,
        input_spec: NodeInputSpec,
        value: Any,
    ) -> None:
        """Validate a literal input value."""
        expected_type = input_spec.type

        # Handle combo inputs (list of valid values)
        if isinstance(expected_type, list):
            if value not in expected_type:
                # Only warn if it's a small list, otherwise could be dynamic
                if len(expected_type) <= 20:
                    result.add_warning(
                        node_id,
                        "value_not_in_list",
                        f"Value '{value}' not in options: {expected_type[:5]}{'...' if len(expected_type) > 5 else ''}",
                        input_name=input_name,
                    )
            return

        # Type-specific validation
        if expected_type == "INT":
            if not isinstance(value, int):
                result.add_error(
                    node_id,
                    "invalid_type",
                    f"Expected INT, got {type(value).__name__}",
                    input_name=input_name,
                )
            elif input_spec.min is not None and value < input_spec.min:
                result.add_error(
                    node_id,
                    "value_out_of_range",
                    f"Value {value} is less than minimum {input_spec.min}",
                    input_name=input_name,
                )
            elif input_spec.max is not None and value > input_spec.max:
                result.add_error(
                    node_id,
                    "value_out_of_range",
                    f"Value {value} is greater than maximum {input_spec.max}",
                    input_name=input_name,
                )

        elif expected_type == "FLOAT":
            if not isinstance(value, (int, float)):
                result.add_error(
                    node_id,
                    "invalid_type",
                    f"Expected FLOAT, got {type(value).__name__}",
                    input_name=input_name,
                )
            elif input_spec.min is not None and value < input_spec.min:
                result.add_error(
                    node_id,
                    "value_out_of_range",
                    f"Value {value} is less than minimum {input_spec.min}",
                    input_name=input_name,
                )
            elif input_spec.max is not None and value > input_spec.max:
                result.add_error(
                    node_id,
                    "value_out_of_range",
                    f"Value {value} is greater than maximum {input_spec.max}",
                    input_name=input_name,
                )

        elif expected_type == "STRING":
            if not isinstance(value, str):
                result.add_error(
                    node_id,
                    "invalid_type",
                    f"Expected STRING, got {type(value).__name__}",
                    input_name=input_name,
                )

        elif expected_type == "BOOLEAN":
            if not isinstance(value, bool):
                result.add_error(
                    node_id,
                    "invalid_type",
                    f"Expected BOOLEAN, got {type(value).__name__}",
                    input_name=input_name,
                )

    @staticmethod
    def _is_connection(value: Any) -> bool:
        """Check if a value is a node connection."""
        return (
            isinstance(value, list)
            and len(value) == 2
            and isinstance(value[0], str)
            and isinstance(value[1], int)
        )


def validate_workflow(
    workflow: dict[str, Any],
    cache: NodeDefCache | None = None,
) -> ValidationResult:
    """Validate a workflow.

    Convenience function that creates a validator and runs validation.

    Args:
        workflow: The workflow in API format
        cache: Optional node definition cache for full validation

    Returns:
        ValidationResult with any errors or warnings
    """
    validator = WorkflowValidator(cache)
    return validator.validate(workflow)
