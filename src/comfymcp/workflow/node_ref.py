"""NodeRef class for referencing nodes with named outputs.

Provides a type-safe way to reference node outputs by name instead of
magic slot indices, making workflow construction more intuitive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from comfymcp.client.types import NodeDef


@dataclass
class NodeRef:
    """Reference to a node in a workflow with named output access.

    NodeRef wraps a node and provides convenient access to its outputs
    by name, automatically converting to the [node_id, slot] format
    that ComfyUI expects.

    Example:
        checkpoint = builder.add_node("CheckpointLoaderSimple",
            ckpt_name="v1-5-pruned.safetensors"
        )

        # Access outputs by name
        model_output = checkpoint.output("MODEL")  # Returns ["1", 0]

        # Or use property shortcuts
        clip_output = checkpoint.CLIP  # Returns ["1", 1]

        # Use in other nodes
        sampler = builder.add_node("KSampler",
            model=checkpoint.MODEL,
            positive=clip_encode.CONDITIONING,
            ...
        )

    Attributes:
        node_id: The unique ID of this node in the workflow
        class_type: The ComfyUI node class type (e.g., "KSampler")
        inputs: The input values provided to this node
        node_def: The full node definition (if available)
    """

    node_id: str
    class_type: str
    inputs: dict[str, Any] = field(default_factory=dict)
    node_def: NodeDef | None = None

    def output(self, name: str) -> list[str | int]:
        """Get a reference to an output by name.

        Args:
            name: The output name (e.g., "MODEL", "CLIP", "IMAGE")

        Returns:
            A list [node_id, slot_index] for use in workflow connections

        Raises:
            ValueError: If the output name is not found
        """
        if self.node_def is None:
            raise ValueError(
                f"Cannot get output by name without node definition. "
                f"Use output_slot() for raw slot access."
            )

        try:
            slot = self.node_def.get_output_slot(name)
            return [self.node_id, slot]
        except ValueError as e:
            available = [o.name for o in self.node_def.outputs]
            raise ValueError(
                f"Output '{name}' not found on {self.class_type}. "
                f"Available outputs: {available}"
            ) from e

    def output_slot(self, slot: int) -> list[str | int]:
        """Get a reference to an output by slot index.

        Use this when you don't have the node definition available,
        or when you need to access outputs by index.

        Args:
            slot: The output slot index (0-based)

        Returns:
            A list [node_id, slot_index] for use in workflow connections
        """
        return [self.node_id, slot]

    @property
    def output_names(self) -> list[str]:
        """Get all output names for this node.

        Returns:
            List of output names, or empty list if node_def not available
        """
        if self.node_def is None:
            return []
        return [o.name for o in self.node_def.outputs]

    @property
    def output_types(self) -> list[str]:
        """Get all output types for this node.

        Returns:
            List of output type names, or empty list if node_def not available
        """
        if self.node_def is None:
            return []
        return [o.type for o in self.node_def.outputs]

    # ==================== Common Output Property Shortcuts ====================
    # These provide convenient access to frequently-used output types

    @property
    def MODEL(self) -> list[str | int]:
        """Shortcut for .output("MODEL")."""
        return self._get_output_by_type_or_name("MODEL")

    @property
    def CLIP(self) -> list[str | int]:
        """Shortcut for .output("CLIP")."""
        return self._get_output_by_type_or_name("CLIP")

    @property
    def VAE(self) -> list[str | int]:
        """Shortcut for .output("VAE")."""
        return self._get_output_by_type_or_name("VAE")

    @property
    def IMAGE(self) -> list[str | int]:
        """Shortcut for .output("IMAGE")."""
        return self._get_output_by_type_or_name("IMAGE")

    @property
    def LATENT(self) -> list[str | int]:
        """Shortcut for .output("LATENT")."""
        return self._get_output_by_type_or_name("LATENT")

    @property
    def CONDITIONING(self) -> list[str | int]:
        """Shortcut for .output("CONDITIONING")."""
        return self._get_output_by_type_or_name("CONDITIONING")

    @property
    def MASK(self) -> list[str | int]:
        """Shortcut for .output("MASK")."""
        return self._get_output_by_type_or_name("MASK")

    @property
    def CONTROL_NET(self) -> list[str | int]:
        """Shortcut for .output("CONTROL_NET")."""
        return self._get_output_by_type_or_name("CONTROL_NET")

    @property
    def AUDIO(self) -> list[str | int]:
        """Shortcut for .output("AUDIO")."""
        return self._get_output_by_type_or_name("AUDIO")

    def _get_output_by_type_or_name(self, name: str) -> list[str | int]:
        """Get output by name, falling back to type matching.

        First tries to find an output with the exact name. If not found,
        looks for an output with a matching type.

        Args:
            name: The output name or type to find

        Returns:
            A list [node_id, slot_index]

        Raises:
            ValueError: If no matching output is found
        """
        if self.node_def is None:
            raise ValueError(
                f"Cannot get output '{name}' without node definition. "
                f"Use output_slot() for raw slot access."
            )

        # First try exact name match
        for output in self.node_def.outputs:
            if output.name == name:
                return [self.node_id, output.slot]

        # Then try type match
        for output in self.node_def.outputs:
            if output.type == name:
                return [self.node_id, output.slot]

        available = [(o.name, o.type) for o in self.node_def.outputs]
        raise ValueError(
            f"No output '{name}' found on {self.class_type}. "
            f"Available outputs: {available}"
        )

    def __getitem__(self, key: str | int) -> list[str | int]:
        """Allow dict-like access to outputs.

        Args:
            key: Output name (str) or slot index (int)

        Returns:
            A list [node_id, slot_index]
        """
        if isinstance(key, int):
            return self.output_slot(key)
        return self.output(key)

    def __repr__(self) -> str:
        outputs_str = ""
        if self.node_def:
            outputs = [f"{o.name}:{o.type}" for o in self.node_def.outputs]
            outputs_str = f", outputs=[{', '.join(outputs)}]"
        return f"NodeRef(id={self.node_id!r}, class={self.class_type!r}{outputs_str})"


def is_node_ref(value: Any) -> bool:
    """Check if a value is a NodeRef."""
    return isinstance(value, NodeRef)


def is_connection(value: Any) -> bool:
    """Check if a value is a node connection [node_id, slot].

    ComfyUI represents connections as 2-element lists where:
    - First element is node ID (string)
    - Second element is output slot index (int)
    """
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
    )
