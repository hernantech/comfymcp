# Datatypes

This document covers the datatypes used in ComfyUI custom nodes for defining inputs and outputs.

## Overview

ComfyUI uses a type system to define how nodes connect to each other. Each input and output has a datatype that determines which connections are valid. When two nodes share compatible types, they can be connected together.

## Built-in Datatypes

ComfyUI provides several built-in datatypes that are commonly used across nodes:

### Core Types

| Type | Description |
|------|-------------|
| `MODEL` | A diffusion model (e.g., Stable Diffusion checkpoint) |
| `CLIP` | A CLIP text encoder model |
| `VAE` | A Variational Autoencoder model |
| `CONDITIONING` | Encoded conditioning information (text embeddings) |
| `LATENT` | Latent image representation |
| `IMAGE` | Image tensor in RGB format (B, H, W, C) |
| `MASK` | Mask tensor (B, H, W) |

### Additional Types

| Type | Description |
|------|-------------|
| `CONTROL_NET` | A ControlNet model |
| `STYLE_MODEL` | A style model (e.g., T2I-Adapter) |
| `GLIGEN` | GLIGEN model for grounded generation |
| `UPSCALE_MODEL` | An upscaling model |
| `CLIP_VISION` | CLIP Vision encoder |
| `CLIP_VISION_OUTPUT` | Output from CLIP Vision encoder |
| `SAMPLER` | A sampler configuration |
| `SIGMAS` | Noise schedule sigmas |
| `NOISE` | Noise tensor |
| `GUIDER` | A guider configuration |

## Primitive Types

ComfyUI also supports primitive Python types that can be used for simple inputs:

```python
# String input
("STRING", {"default": "", "multiline": False})

# Integer input
("INT", {"default": 0, "min": 0, "max": 100, "step": 1})

# Float input
("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1})

# Boolean input
("BOOLEAN", {"default": True})
```

### String Options

```python
("STRING", {
    "default": "",
    "multiline": True,  # Enables multi-line text input
    "placeholder": "Enter text here...",  # Placeholder text
    "dynamicPrompts": True,  # Enable dynamic prompt syntax
})
```

### Numeric Options

```python
# Integer with display options
("INT", {
    "default": 512,
    "min": 64,
    "max": 4096,
    "step": 64,
    "display": "number",  # or "slider"
})

# Float with precision
("FLOAT", {
    "default": 0.5,
    "min": 0.0,
    "max": 1.0,
    "step": 0.01,
    "round": 0.001,  # Rounding precision
    "display": "slider",
})
```

## Combo Types

Combo types allow users to select from a predefined list of options:

```python
# Static list of options
(["option1", "option2", "option3"], {"default": "option1"})

# Dynamic options from a function
(@classmethod
def INPUT_TYPES(cls):
    return {
        "required": {
            "scheduler": (comfy.samplers.SCHEDULER_NAMES, ),
            "sampler": (comfy.samplers.SAMPLER_NAMES, ),
        }
    })
```

## Custom Datatypes

You can define your own datatypes for custom node connections:

```python
class MyCustomNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "my_data": ("MY_CUSTOM_TYPE", ),
            }
        }

    RETURN_TYPES = ("MY_CUSTOM_TYPE",)
    RETURN_NAMES = ("output_data",)
    FUNCTION = "process"
    CATEGORY = "custom"

    def process(self, my_data):
        # Process the custom data
        result = do_something(my_data)
        return (result,)
```

Custom types are identified by their string name. Two nodes with matching type strings can connect together.

## Type Wildcards

The `*` wildcard type can connect to any other type:

```python
RETURN_TYPES = ("*",)  # Can connect to any input
```

This is useful for pass-through nodes or debugging utilities.

## Optional Inputs

Inputs can be marked as optional by placing them in the `"optional"` dictionary:

```python
@classmethod
def INPUT_TYPES(cls):
    return {
        "required": {
            "image": ("IMAGE",),
        },
        "optional": {
            "mask": ("MASK",),
            "strength": ("FLOAT", {"default": 1.0}),
        }
    }
```

Optional inputs will be `None` if not connected.

## Hidden Inputs

Hidden inputs provide special functionality without appearing in the UI:

```python
@classmethod
def INPUT_TYPES(cls):
    return {
        "required": {
            "image": ("IMAGE",),
        },
        "hidden": {
            "prompt": "PROMPT",
            "extra_pnginfo": "EXTRA_PNGINFO",
            "unique_id": "UNIQUE_ID",
        }
    }
```

### Common Hidden Types

| Type | Description |
|------|-------------|
| `PROMPT` | The entire workflow prompt data |
| `EXTRA_PNGINFO` | Extra PNG metadata |
| `UNIQUE_ID` | The unique identifier of this node instance |

## Image Format

Images in ComfyUI use a specific tensor format:

- Shape: `(batch, height, width, channels)`
- Channels: RGB (3 channels)
- Value range: `0.0` to `1.0`
- Dtype: `torch.float32`

```python
# Example: Creating an image tensor
import torch

# Single RGB image, 512x512
image = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
```

## Mask Format

Masks use a similar format without the channel dimension:

- Shape: `(batch, height, width)`
- Value range: `0.0` to `1.0`
- Dtype: `torch.float32`

```python
# Example: Creating a mask tensor
mask = torch.ones((1, 512, 512), dtype=torch.float32)
```

## Latent Format

Latent images are stored as dictionaries containing the samples tensor:

```python
latent = {
    "samples": torch.zeros((1, 4, 64, 64)),  # (batch, channels, height/8, width/8)
}
```

The latent space is typically 1/8 the resolution of the pixel space for Stable Diffusion models.

## Conditioning Format

Conditioning is a list of tuples containing the conditioning tensor and a pooled output dictionary:

```python
conditioning = [
    [
        cond_tensor,  # Shape: (batch, tokens, embedding_dim)
        {"pooled_output": pooled_tensor}  # Pooled CLIP output
    ]
]
```

## Type Conversion

When you need to work with different representations:

```python
# Image to Mask (use first channel or convert to grayscale)
def image_to_mask(image):
    # image shape: (B, H, W, C)
    # Convert to grayscale
    mask = 0.299 * image[:,:,:,0] + 0.587 * image[:,:,:,1] + 0.114 * image[:,:,:,2]
    return mask

# Mask to Image (expand to 3 channels)
def mask_to_image(mask):
    # mask shape: (B, H, W)
    return mask.unsqueeze(-1).expand(-1, -1, -1, 3)
```

## Best Practices

1. **Use standard types when possible**: Prefer built-in types like `IMAGE`, `MASK`, `MODEL` for compatibility with other nodes.

2. **Document custom types**: If you create custom types, document what data format they expect.

3. **Validate inputs**: Check that inputs match expected shapes and ranges in your node's processing function.

4. **Handle batches**: Always account for the batch dimension in your tensor operations.

5. **Type naming conventions**: Use uppercase snake_case for type names (e.g., `MY_CUSTOM_TYPE`).
