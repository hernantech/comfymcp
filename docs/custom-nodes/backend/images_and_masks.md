# Images, Latents, and Masks - ComfyUI Documentation

## Overview

This documentation covers how to work with three key data types in ComfyUI: images, latents, and masks. Understanding `torch.Tensor` class is essential for working with these datatypes.

## Images

An IMAGE is represented as a `torch.Tensor` with shape `[B,H,W,C]` where C=3 (representing RGB channels).

**Key Point:** "If you are going to save or load images, you will need to convert to and from `PIL.Image` format"

When working with images, be aware that some PyTorch operations use channel-first format `[B,C,H,W]` for computational efficiency, so careful conversion may be necessary.

### Working with PIL.Image

To load and save images, import PIL:

```python
from PIL import Image, ImageOps
```

## Masks

A MASK is a `torch.Tensor` with shape `[B,H,W]`. Masks typically contain binary values (0 or 1) to indicate which pixels should undergo specific operations, though values between 0-1 can indicate varying degrees of masking.

### Masks from the Load Image Node

The LoadImage node uses an image's alpha channel to create masks. Values are normalized to [0,1] range as torch.float32 and then inverted. When images lack an alpha channel (like JPEGs), LoadImage creates a default mask with shape `[1, 64, 64]`.

### Understanding Mask Shapes

Single-channel representations typically use shape `[H,W]` in libraries like numpy and PIL. Therefore, mask batches have three dimensions: `[B, H, W]` rather than four. To match shapes for operations, you may need to unsqueeze dimensions: use `unsqueeze(-1)` for the C dimension and `unsqueeze(0)` for the B dimension.

## Latents

A LATENT is a dictionary where the latent sample is accessed via the key `samples` and has shape `[B,C,H,W]` with C=4.

**Important distinction:** "LATENT is channel first, IMAGE is channel last"
