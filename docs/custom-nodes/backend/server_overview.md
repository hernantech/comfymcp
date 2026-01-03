# Backend Server Overview

> Source: https://docs.comfy.org/custom-nodes/backend/server_overview

This document provides an overview of the ComfyUI backend server and how custom nodes interact with it.

## Node Class Structure

Every custom node is a Python class with specific attributes and methods:

### Required Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `INPUT_TYPES` | classmethod | Defines node inputs |
| `RETURN_TYPES` | tuple | Output types |
| `FUNCTION` | str | Processing method name |
| `CATEGORY` | str | Menu category |

### Optional Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `RETURN_NAMES` | tuple | Display names for outputs |
| `OUTPUT_NODE` | bool | Terminal node flag |
| `INPUT_IS_LIST` | bool | Receive inputs as lists |
| `OUTPUT_IS_LIST` | tuple | Outputs are lists |

## INPUT_TYPES Structure

```python
@classmethod
def INPUT_TYPES(cls):
    return {
        "required": {
            "image": ("IMAGE",),
            "strength": ("FLOAT", {
                "default": 1.0,
                "min": 0.0,
                "max": 2.0,
                "step": 0.1
            }),
        },
        "optional": {
            "mask": ("MASK",),
        },
        "hidden": {
            "node_id": "UNIQUE_ID",
        }
    }
```

## Processing Method

The method named in `FUNCTION` receives inputs as keyword arguments:

```python
def process(self, image, strength, mask=None):
    # Process inputs
    result = self.apply_effect(image, strength, mask)
    # Return tuple matching RETURN_TYPES
    return (result,)
```

## Node Categories

Organize nodes in hierarchical categories:
- `"image"` - Image operations
- `"image/transform"` - Image transformations
- `"conditioning"` - Prompt conditioning
- `"latent"` - Latent space operations
