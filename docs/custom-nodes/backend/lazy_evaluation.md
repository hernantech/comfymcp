# Lazy Evaluation

> Source: https://docs.comfy.org/custom-nodes/backend/lazy_evaluation

This document explains lazy evaluation in ComfyUI custom nodes, allowing inputs to be evaluated only when needed.

## Overview

Lazy evaluation allows nodes to defer the computation of certain inputs until they are actually required. This is useful for:
- Conditional logic where some inputs may not be needed
- Performance optimization
- Implementing control flow

## Enabling Lazy Inputs

Mark inputs as lazy in INPUT_TYPES:

```python
@classmethod
def INPUT_TYPES(cls):
    return {
        "required": {
            "condition": ("BOOLEAN",),
            "if_true": ("IMAGE", {"lazy": True}),
            "if_false": ("IMAGE", {"lazy": True}),
        },
    }

FUNCTION = "execute"
```

## Checking Input Availability

Lazy inputs may not be computed yet. Check and request them:

```python
def check_lazy_status(self, condition, if_true, if_false):
    # Request only the needed input
    if condition:
        if if_true is None:
            return ["if_true"]  # Request this input
    else:
        if if_false is None:
            return ["if_false"]  # Request this input
    return []  # All needed inputs available

def execute(self, condition, if_true, if_false):
    return (if_true if condition else if_false,)
```

## Use Cases

### Conditional Branching

Only evaluate the branch that will be used:

```python
def select_branch(self, selector, option_a, option_b, option_c):
    options = [option_a, option_b, option_c]
    return (options[selector],)
```

### Optional Processing

Skip expensive computation when not needed:

```python
def optional_enhance(self, image, enable_enhance, enhanced_image):
    if enable_enhance:
        return (enhanced_image,)
    return (image,)
```

## Best Practices

1. Use lazy evaluation for genuinely optional inputs
2. Always handle the case where lazy inputs are None
3. Return the list of required inputs from check method
4. Document which inputs use lazy evaluation
