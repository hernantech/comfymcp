"""Image-to-image workflow template.

Provides a configurable template for transforming images using
prompts and a Stable Diffusion model.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from comfymcp.templates.base import WorkflowTemplate
from comfymcp.workflow import WorkflowBuilder

if TYPE_CHECKING:
    from comfymcp.workflow import NodeDefCache


@dataclass
class Img2ImgParams:
    """Parameters for image-to-image generation.

    Attributes:
        checkpoint: Checkpoint filename (required)
        image: Input image filename in ComfyUI input folder (required)
        positive_prompt: Positive prompt text (required)
        negative_prompt: Negative prompt text
        denoise: Denoise strength (0.0 to 1.0)
        steps: Number of sampling steps
        cfg: CFG scale (classifier-free guidance)
        sampler_name: Name of the sampler to use
        scheduler: Scheduler type
        seed: Random seed (-1 for random)
        batch_size: Number of images to generate
    """

    checkpoint: str
    image: str
    positive_prompt: str
    negative_prompt: str = ""
    denoise: float = 0.75
    steps: int = 20
    cfg: float = 7.0
    sampler_name: str = "euler"
    scheduler: str = "normal"
    seed: int = -1
    batch_size: int = 1


@dataclass
class Img2ImgTemplate(WorkflowTemplate):
    """Template for image-to-image workflows.

    Creates a standard Stable Diffusion img2img workflow with:
    - CheckpointLoaderSimple
    - LoadImage
    - VAEEncode
    - CLIPTextEncode (positive)
    - CLIPTextEncode (negative)
    - KSampler
    - VAEDecode
    - SaveImage

    Example:
        template = Img2ImgTemplate(
            checkpoint="v1-5-pruned.safetensors",
            image="input.png",
            positive_prompt="a beautiful landscape",
            negative_prompt="ugly, blurry",
            denoise=0.75,
            steps=20,
        )
        workflow = template.build()
    """

    checkpoint: str
    image: str
    positive_prompt: str
    negative_prompt: str = ""
    denoise: float = 0.75
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
        if not self.image:
            errors.append("image is required")
        if not self.positive_prompt:
            errors.append("positive_prompt is required")
        if self.denoise < 0.0 or self.denoise > 1.0:
            errors.append("denoise must be between 0.0 and 1.0")
        if self.steps <= 0:
            errors.append("steps must be positive")
        if self.cfg < 0:
            errors.append("cfg must be non-negative")
        if self.batch_size <= 0:
            errors.append("batch_size must be positive")

        return errors

    def build(self, cache: NodeDefCache | None = None) -> dict[str, Any]:
        """Build the image-to-image workflow.

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

        # Load input image
        load_image = builder.add_node(
            "LoadImage",
            image=self.image,
        )

        # Encode image to latent space
        vae_encode = builder.add_node(
            "VAEEncode",
            pixels=load_image.output_slot(0),  # IMAGE output
            vae=checkpoint.output_slot(2),  # VAE output
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

        # Sample with denoise
        sampler = builder.add_node(
            "KSampler",
            model=checkpoint.output_slot(0),  # MODEL output
            positive=positive.output_slot(0),  # CONDITIONING output
            negative=negative.output_slot(0),  # CONDITIONING output
            latent_image=vae_encode.output_slot(0),  # LATENT output
            seed=seed,
            steps=self.steps,
            cfg=self.cfg,
            sampler_name=self.sampler_name,
            scheduler=self.scheduler,
            denoise=self.denoise,
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
    def from_params(cls, params: Img2ImgParams) -> Img2ImgTemplate:
        """Create a template from an Img2ImgParams object.

        Args:
            params: The parameters for the template.

        Returns:
            A configured Img2ImgTemplate instance.
        """
        return cls(
            checkpoint=params.checkpoint,
            image=params.image,
            positive_prompt=params.positive_prompt,
            negative_prompt=params.negative_prompt,
            denoise=params.denoise,
            steps=params.steps,
            cfg=params.cfg,
            sampler_name=params.sampler_name,
            scheduler=params.scheduler,
            seed=params.seed,
            batch_size=params.batch_size,
        )
