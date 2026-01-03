# V3 Migration Guide

This guide explains how to migrate your existing V1 nodes to the new V3 schema in ComfyUI.

## Overview

The V3 schema introduces structural improvements to custom node development:

- **Class-based inputs/outputs** replace dictionary definitions
- **Standardized execution** via an `execute` class method
- **Extension-based registration** using `comfy_entrypoint()` instead of node mappings
- **No instance state** exposure - all methods are class methods

## Key Changes

### 1. Base Class

Nodes now inherit from `io.ComfyNode` instead of a generic class.

**V1 Style:**
```python
class MyNode:
    # Node definition
    pass
```

**V3 Style:**
```python
from comfy.nodes import io

class MyNode(io.ComfyNode):
    # Node definition
    pass
```

### 2. Schema Definition

The method `define_schema()` replaces scattered properties. Node properties like node id, display name, category, etc. that were assigned in different places in code such as dictionaries and class properties are now kept together via the `Schema` class.

**V1 Style:**
```python
class MyNode:
    CATEGORY = "example"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "value": ("FLOAT", {"default": 1.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    FUNCTION = "process"
```

**V3 Style:**
```python
from comfy.nodes import io

class MyNode(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="MyNode",
            display_name="My Node",
            category="example",
            inputs=[
                io.Image.Input("image"),
                io.Float.Input("value", default=1.0),
            ],
            outputs=[
                io.Image.Output("output_image"),
            ],
        )
```

### 3. Input/Output Objects

Instead of dictionaries or strings, inputs and outputs use object-oriented type classes like `io.Image.Input()` and `io.Model.Output()`.

#### Available Type Classes

| V1 Type String | V3 Type Class |
|----------------|---------------|
| `"IMAGE"` | `io.Image` |
| `"LATENT"` | `io.Latent` |
| `"MODEL"` | `io.Model` |
| `"CONDITIONING"` | `io.Conditioning` |
| `"VAE"` | `io.Vae` |
| `"CLIP"` | `io.Clip` |
| `"STRING"` | `io.String` |
| `"INT"` | `io.Int` |
| `"FLOAT"` | `io.Float` |
| `"BOOLEAN"` | `io.Boolean` |
| `("option1", "option2")` | `io.Combo` |

### 4. Standardized Execution

The execute method becomes a required class method with consistent naming.

**V1 Style:**
```python
class MyNode:
    FUNCTION = "process"

    def process(self, image, value):
        # Process inputs
        result = do_something(image, value)
        return (result,)
```

**V3 Style:**
```python
class MyNode(io.ComfyNode):
    @classmethod
    def execute(cls, image, value):
        # Process inputs
        result = do_something(image, value)
        return io.NodeOutput(output_image=result)
```

### 5. Extension Registration

Instead of mappings dictionaries, you create a `ComfyExtension` class with a `comfy_entrypoint()` function that returns the extension instance.

**V1 Style (\_\_init\_\_.py):**
```python
from .nodes import MyNode, AnotherNode

NODE_CLASS_MAPPINGS = {
    "MyNode": MyNode,
    "AnotherNode": AnotherNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MyNode": "My Custom Node",
    "AnotherNode": "Another Custom Node",
}
```

**V3 Style (\_\_init\_\_.py):**
```python
from comfy.nodes import io

class MyExtension(io.ComfyExtension):
    @classmethod
    def get_node_list(cls):
        from .nodes import MyNode, AnotherNode
        return [MyNode, AnotherNode]

def comfy_entrypoint():
    return MyExtension()
```

## Migration Process

Follow these six steps to migrate your V1 nodes to V3:

### Step 1: Inherit from ComfyNode

Change your node class to inherit from `io.ComfyNode`:

```python
from comfy.nodes import io

class MyNode(io.ComfyNode):
    pass
```

### Step 2: Convert INPUT_TYPES to define_schema()

Replace the `INPUT_TYPES` class method with `define_schema()` which returns a Schema object with organized properties:

```python
@classmethod
def define_schema(cls):
    return io.Schema(
        node_id="MyNode",
        display_name="My Node",
        category="example",
        inputs=[
            # Define inputs here
        ],
        outputs=[
            # Define outputs here
        ],
    )
```

### Step 3: Update Execute Method

Convert your processing function to use the `@classmethod` decorator and return `io.NodeOutput`:

```python
@classmethod
def execute(cls, **kwargs):
    # Your processing logic
    return io.NodeOutput(output_name=result)
```

### Step 4: Remap Properties

| V1 Property | V3 Equivalent |
|-------------|---------------|
| `RETURN_TYPES` | `outputs` in Schema |
| `RETURN_NAMES` | Output names in `io.Type.Output("name")` |
| `CATEGORY` | `category` in Schema |
| `FUNCTION` | Always `execute` |
| `OUTPUT_NODE` | `is_output_node` in Schema |
| `INPUT_IS_LIST` | Per-input configuration |
| `OUTPUT_IS_LIST` | Per-output configuration |

### Step 5: Rename Special Methods

| V1 Method | V3 Method | Notes |
|-----------|-----------|-------|
| `VALIDATE_INPUTS` | `validate_inputs` | Same signature |
| `IS_CHANGED` | `fingerprint_inputs` | Logic is reversed |
| `check_lazy_status` | `check_lazy_status` | Becomes a class method |

### Step 6: Create Extension Class

Create a `ComfyExtension` class with `get_node_list()` and define `comfy_entrypoint()`:

```python
from comfy.nodes import io

class MyExtension(io.ComfyExtension):
    @classmethod
    def get_node_list(cls):
        return [MyNode, AnotherNode]

def comfy_entrypoint():
    return MyExtension()
```

## Complete Migration Example

### Before (V1)

```python
# nodes.py
class BrightnessAdjuster:
    CATEGORY = "image/adjustment"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "brightness": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("adjusted_image",)
    FUNCTION = "adjust"

    def adjust(self, image, brightness):
        result = image * brightness
        return (result,)

# __init__.py
from .nodes import BrightnessAdjuster

NODE_CLASS_MAPPINGS = {
    "BrightnessAdjuster": BrightnessAdjuster,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BrightnessAdjuster": "Brightness Adjuster",
}
```

### After (V3)

```python
# nodes.py
from comfy.nodes import io

class BrightnessAdjuster(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="BrightnessAdjuster",
            display_name="Brightness Adjuster",
            category="image/adjustment",
            inputs=[
                io.Image.Input("image"),
                io.Float.Input("brightness", default=1.0, min=0.0, max=2.0),
            ],
            outputs=[
                io.Image.Output("adjusted_image"),
            ],
        )

    @classmethod
    def execute(cls, image, brightness):
        result = image * brightness
        return io.NodeOutput(adjusted_image=result)

# __init__.py
from comfy.nodes import io

class ImageAdjustmentExtension(io.ComfyExtension):
    @classmethod
    def get_node_list(cls):
        from .nodes import BrightnessAdjuster
        return [BrightnessAdjuster]

def comfy_entrypoint():
    return ImageAdjustmentExtension()
```

## Type System

V3 provides explicit type classes instead of string-based V1 types, enabling better type safety and UI generation.

### Input Configuration

Inputs can be configured with various options:

```python
io.Float.Input(
    "value",
    default=1.0,
    min=0.0,
    max=10.0,
    step=0.1,
    tooltip="Adjust this value between 0 and 10"
)

io.Combo.Input(
    "mode",
    options=["option1", "option2", "option3"],
    default="option1"
)

io.String.Input(
    "text",
    multiline=True,
    default=""
)
```

### Optional and Hidden Inputs

```python
io.Schema(
    inputs=[
        io.Image.Input("required_image"),  # Required by default
        io.Image.Input("optional_image", optional=True),
        io.String.Input("hidden_value", hidden=True),
    ],
)
```

## Backwards Compatibility

The V3 schema supports future API development while maintaining backwards compatibility through versioning. V1 nodes will continue to work, but new development should use V3 for:

- Better type safety
- Cleaner code organization
- Future feature compatibility
- Improved tooling support

## Additional Resources

- [Custom Nodes Overview](/custom-nodes/overview)
- [Getting Started Walkthrough](/custom-nodes/walkthrough)
- [Backend Properties](/custom-nodes/backend/properties)
- [Data Types Reference](/custom-nodes/backend/datatypes)
