"""WorkflowBuilder for programmatic ComfyUI workflow construction.

Provides a type-safe, intuitive API for building ComfyUI workflows
with named outputs and automatic ID management.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from comfymcp.workflow.node_ref import NodeRef, is_connection, is_node_ref
from comfymcp.workflow.validation import ValidationResult, WorkflowValidator

if TYPE_CHECKING:
    from comfymcp.workflow.node_defs import NodeDefCache


class WorkflowBuilder:
    """Builder for creating ComfyUI workflows programmatically.

    Provides a fluent interface for constructing workflows with:
    - Automatic node ID generation
    - Named output access via NodeRef
    - Type validation (when cache is provided)
    - Automatic NodeRef -> connection conversion

    Example:
        # Create builder with node cache for validation
        builder = WorkflowBuilder(cache)

        # Add nodes and connect them by name
        checkpoint = builder.add_node("CheckpointLoaderSimple",
            ckpt_name="v1-5-pruned.safetensors"
        )

        empty_latent = builder.add_node("EmptyLatentImage",
            width=512, height=512, batch_size=1
        )

        positive = builder.add_node("CLIPTextEncode",
            clip=checkpoint.CLIP,
            text="a beautiful landscape"
        )

        negative = builder.add_node("CLIPTextEncode",
            clip=checkpoint.CLIP,
            text="ugly, blurry"
        )

        sampler = builder.add_node("KSampler",
            model=checkpoint.MODEL,
            positive=positive.CONDITIONING,
            negative=negative.CONDITIONING,
            latent_image=empty_latent.LATENT,
            seed=42,
            steps=20,
            cfg=7.5,
            sampler_name="euler",
            scheduler="normal",
            denoise=1.0
        )

        decode = builder.add_node("VAEDecode",
            samples=sampler.LATENT,
            vae=checkpoint.VAE
        )

        save = builder.add_node("SaveImage",
            images=decode.IMAGE,
            filename_prefix="output"
        )

        # Build the workflow
        workflow = builder.build()

        # Validate before submission
        result = builder.validate()
        if result.valid:
            # Submit to ComfyUI
            ...
    """

    def __init__(
        self,
        cache: NodeDefCache | None = None,
        id_prefix: str = "",
    ) -> None:
        """Initialize the workflow builder.

        Args:
            cache: Node definition cache for validation and output lookups.
                   If not provided, NodeRefs won't have output information.
            id_prefix: Optional prefix for generated node IDs
        """
        self.cache = cache
        self.id_prefix = id_prefix
        self._nodes: dict[str, dict[str, Any]] = {}
        self._node_refs: dict[str, NodeRef] = {}
        self._id_counter = 1

    def _generate_id(self) -> str:
        """Generate a unique node ID."""
        node_id = f"{self.id_prefix}{self._id_counter}"
        self._id_counter += 1
        return node_id

    def add_node(
        self,
        class_type: str,
        node_id: str | None = None,
        **inputs: Any,
    ) -> NodeRef:
        """Add a node to the workflow.

        Args:
            class_type: The ComfyUI node class type (e.g., "KSampler")
            node_id: Optional custom node ID. Auto-generated if not provided.
            **inputs: Node inputs as keyword arguments.
                      NodeRef values are automatically converted to connections.

        Returns:
            NodeRef for this node, allowing access to its outputs

        Raises:
            ValueError: If node_id already exists or class_type is unknown
        """
        # Generate or validate node ID
        if node_id is None:
            node_id = self._generate_id()
        elif node_id in self._nodes:
            raise ValueError(f"Node ID '{node_id}' already exists in workflow")

        # Get node definition if cache is available
        node_def = None
        if self.cache and self.cache.is_loaded:
            node_def = self.cache.get(class_type)
            if node_def is None:
                raise ValueError(
                    f"Unknown node type: {class_type}. "
                    f"Ensure the node cache is refreshed."
                )

        # Process inputs - convert NodeRefs to connections
        processed_inputs = self._process_inputs(inputs)

        # Create the node config
        self._nodes[node_id] = {
            "class_type": class_type,
            "inputs": processed_inputs,
        }

        # Create and store the NodeRef
        node_ref = NodeRef(
            node_id=node_id,
            class_type=class_type,
            inputs=processed_inputs,
            node_def=node_def,
        )
        self._node_refs[node_id] = node_ref

        return node_ref

    def _process_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process inputs, converting NodeRefs to connection format.

        Args:
            inputs: Raw input dictionary

        Returns:
            Processed inputs with NodeRefs converted to [node_id, slot]
        """
        result = {}

        for name, value in inputs.items():
            if is_node_ref(value):
                # If it's a NodeRef, use first output (slot 0)
                result[name] = [value.node_id, 0]
            elif is_connection(value):
                # Already in connection format
                result[name] = value
            else:
                # Regular value
                result[name] = value

        return result

    def get_node(self, node_id: str) -> NodeRef | None:
        """Get a NodeRef by its ID.

        Args:
            node_id: The node ID to look up

        Returns:
            The NodeRef if found, None otherwise
        """
        return self._node_refs.get(node_id)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the workflow.

        Note: This does not update connections from other nodes.
        Those will fail validation.

        Args:
            node_id: The node ID to remove

        Returns:
            True if the node was removed, False if not found
        """
        if node_id in self._nodes:
            del self._nodes[node_id]
            del self._node_refs[node_id]
            return True
        return False

    def update_input(
        self,
        node_id: str,
        input_name: str,
        value: Any,
    ) -> None:
        """Update an input on an existing node.

        Args:
            node_id: The node to update
            input_name: The input name to update
            value: The new value (can be a NodeRef, connection, or literal)

        Raises:
            KeyError: If the node doesn't exist
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not found in workflow")

        # Process the value
        if is_node_ref(value):
            processed_value = [value.node_id, 0]
        elif is_connection(value):
            processed_value = value
        else:
            processed_value = value

        self._nodes[node_id]["inputs"][input_name] = processed_value
        self._node_refs[node_id].inputs[input_name] = processed_value

    def set_seed(
        self,
        node_id: str | None = None,
        seed: int | None = None,
        input_name: str = "seed",
    ) -> int:
        """Set seed for sampler nodes.

        Args:
            node_id: Specific node to set seed on, or None for all samplers
            seed: Seed value, or None for random
            input_name: The seed input name (usually "seed" or "noise_seed")

        Returns:
            The seed value that was set
        """
        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        if node_id is not None:
            if node_id in self._nodes:
                self._nodes[node_id]["inputs"][input_name] = seed
        else:
            # Set on all nodes that have a seed input
            for nid, config in self._nodes.items():
                if input_name in config["inputs"]:
                    config["inputs"][input_name] = seed

        return seed

    def build(self) -> dict[str, Any]:
        """Build and return the workflow in ComfyUI API format.

        Returns:
            Dictionary mapping node IDs to node configurations
        """
        return dict(self._nodes)

    def validate(self) -> ValidationResult:
        """Validate the workflow.

        Returns:
            ValidationResult with any errors or warnings
        """
        validator = WorkflowValidator(self.cache)
        return validator.validate(self._nodes)

    def clear(self) -> None:
        """Clear all nodes from the workflow."""
        self._nodes.clear()
        self._node_refs.clear()
        self._id_counter = 1

    @property
    def node_count(self) -> int:
        """Get the number of nodes in the workflow."""
        return len(self._nodes)

    @property
    def nodes(self) -> list[NodeRef]:
        """Get all nodes as NodeRefs."""
        return list(self._node_refs.values())

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._nodes

    def __repr__(self) -> str:
        return f"WorkflowBuilder(nodes={len(self._nodes)})"


def build_workflow(
    nodes: list[dict[str, Any]],
    cache: NodeDefCache | None = None,
) -> dict[str, Any]:
    """Convenience function to build a workflow from a list of node specs.

    Each node spec should have:
    - "class_type": The node class
    - "id" (optional): Custom node ID
    - Other keys are treated as inputs

    Args:
        nodes: List of node specifications
        cache: Optional node definition cache

    Returns:
        The workflow in ComfyUI API format

    Example:
        workflow = build_workflow([
            {"class_type": "CheckpointLoaderSimple", "ckpt_name": "v1-5.safetensors"},
            {"class_type": "EmptyLatentImage", "width": 512, "height": 512, "batch_size": 1},
            {"class_type": "KSampler", "model": ["1", 0], ...},
        ])
    """
    builder = WorkflowBuilder(cache)

    for spec in nodes:
        class_type = spec.pop("class_type")
        node_id = spec.pop("id", None)
        builder.add_node(class_type, node_id=node_id, **spec)

    return builder.build()
