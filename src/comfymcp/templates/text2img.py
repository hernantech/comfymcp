"""Text-to-image workflow template.

Provides a configurable template for generating images from text prompts
using a standard Stable Diffusion workflow.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from comfymcp.templates.base import WorkflowTemplate
from comfymcp.workflow import WorkflowBuilder

if TYPE_CHECKING:
    from comfymcp.workflow import NodeDefCache


@dataclass
class Text2ImgParams:
    """Parameters for text-to-image generation.

    Attributes:
        checkpoint: Checkpoint filename (required)
        positive_prompt: Positive prompt text (required)
        negative_prompt: Negative prompt text
        width: Image width in pixels
        height: Image height in pixels
        steps: Number of sampling steps
        cfg: CFG scale (classifier-free guidance)
        sampler_name: Name of the sampler to use
        scheduler: Scheduler type
        seed: Random seed (-1 for random)
        batch_size: Number of images to generate
    """

    checkpoint: str
    positive_prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg: float = 7.0
    sampler_name: str = "euler"
    scheduler: str = "normal"
    seed: int = -1
    batch_size: int = 1


@dataclass
class Text2ImgTemplate(WorkflowTemplate):
    """Template for text-to-image workflows.

    Creates a standard Stable Diffusion txt2img workflow with:
    - CheckpointLoaderSimple
    - EmptyLatentImage
    - CLIPTextEncode (positive)
    - CLIPTextEncode (negative)
    - KSampler
    - VAEDecode
    - SaveImage

    Example:
        template = Text2ImgTemplate(
            checkpoint="v1-5-pruned.safetensors",
            positive_prompt="a beautiful landscape",
            negative_prompt="ugly, blurry",
            width=512,
            height=512,
            steps=20,
        )
        workflow = template.build()
    """

    checkpoint: str
    positive_prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg: float = 7.0
    sampler_name: str = "euler"
    scheduler: str = "normal"
    seed: int = -1
    batch_size: int = 1
    filename_prefix: str = "ComfyUI"

    def validate_params(self) -> list[str]:
        """Validate template parameters.

        Returns:
            List of validation error messages.
        """
        errors = []

        if not self.checkpoint:
            errors.append("checkpoint is required")
        if not self.positive_prompt:
            errors.append("positive_prompt is required")
        if self.width <= 0:
            errors.append("width must be positive")
        if self.height <= 0:
            errors.append("height must be positive")
        if self.steps <= 0:
            errors.append("steps must be positive")
        if self.cfg < 0:
            errors.append("cfg must be non-negative")
        if self.batch_size <= 0:
            errors.append("batch_size must be positive")

        return errors

    def build(self, cache: NodeDefCache | None = None) -> dict[str, Any]:
        """Build the text-to-image workflow.

        Args:
            cache: Optional NodeDefCache for validation and output lookups.

        Returns:
            A workflow dict in ComfyUI API format.
        """
        builder = WorkflowBuilder(cache)

        # Handle random seed
        seed = self.seed if self.seed >= 0 else random.randint(0, 2**32 - 1)

        # Load checkpoint
        checkpoint = builder.add_node(
            "CheckpointLoaderSimple",
            ckpt_name=self.checkpoint,
        )

        # Create empty latent image
        empty_latent = builder.add_node(
            "EmptyLatentImage",
            width=self.width,
            height=self.height,
            batch_size=self.batch_size,
        )

        # Encode positive prompt
        positive = builder.add_node(
            "CLIPTextEncode",
            clip=checkpoint.output_slot(1),  # CLIP output
            text=self.positive_prompt,
        )

        # Encode negative prompt
        negative = builder.add_node(
            "CLIPTextEncode",
            clip=checkpoint.output_slot(1),  # CLIP output
            text=self.negative_prompt,
        )

        # Sample
        sampler = builder.add_node(
            "KSampler",
            model=checkpoint.output_slot(0),  # MODEL output
            positive=positive.output_slot(0),  # CONDITIONING output
            negative=negative.output_slot(0),  # CONDITIONING output
            latent_image=empty_latent.output_slot(0),  # LATENT output
            seed=seed,
            steps=self.steps,
            cfg=self.cfg,
            sampler_name=self.sampler_name,
            scheduler=self.scheduler,
            denoise=1.0,
        )

        # Decode latent to image
        decode = builder.add_node(
            "VAEDecode",
            samples=sampler.output_slot(0),  # LATENT output
            vae=checkpoint.output_slot(2),  # VAE output
        )

        # Save image
        builder.add_node(
            "SaveImage",
            images=decode.output_slot(0),  # IMAGE output
            filename_prefix=self.filename_prefix,
        )

        return builder.build()

    @classmethod
    def from_params(cls, params: Text2ImgParams) -> Text2ImgTemplate:
        """Create a template from a Text2ImgParams object.

        Args:
            params: The parameters for the template.

        Returns:
            A configured Text2ImgTemplate instance.
        """
        return cls(
            checkpoint=params.checkpoint,
            positive_prompt=params.positive_prompt,
            negative_prompt=params.negative_prompt,
            width=params.width,
            height=params.height,
            steps=params.steps,
            cfg=params.cfg,
            sampler_name=params.sampler_name,
            scheduler=params.scheduler,
            seed=params.seed,
            batch_size=params.batch_size,
        )
