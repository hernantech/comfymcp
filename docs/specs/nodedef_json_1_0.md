# ComfyUI Node Definition JSON Schema v1.0

> Source: https://docs.comfy.org/specs/nodedef_json_1_0

This document defines the JSON schema structure for ComfyUI nodes.

## Core Structure

A ComfyNode definition requires these essential fields:

| Field | Description |
|-------|-------------|
| **name** | The node's identifier |
| **display_name** | Human-readable name |
| **description** | What the node does |
| **category** | Classification category |
| **output_node** | Boolean indicating if it's a terminal node |
| **python_module** | Associated Python module reference |

## Input Configuration

Nodes support three input categories:

1. **Required inputs**: Must be provided for node execution
2. **Optional inputs**: Can be omitted
3. **Hidden inputs**: Internal parameters

## Supported Input Types

The schema accommodates multiple parameter types:

### INT (Integer)
Integer values with optional configuration:
- `min`: Minimum value
- `max`: Maximum value
- `step`: Increment step
- Display modes: `slider`, `number`, `knob`

### FLOAT (Decimal)
Decimal numbers with:
- `min`: Minimum value
- `max`: Maximum value
- `step`: Increment step
- Rounding options

### BOOLEAN
True/false toggles with:
- Custom labels for on/off states

### STRING
Text inputs with:
- `multiline`: Enable multi-line text
- `placeholder`: Placeholder text
- `default`: Default value

### COMBO
Dropdown selections from predefined arrays:
- Array of options to choose from

### Custom Types
Generic string-based type references for custom data types.

## Advanced Features

Input parameters support additional options:

| Feature | Description |
|---------|-------------|
| **Default values** | Pre-set values for inputs |
| **Input enforcement** | Force input type validation |
| **Tooltips** | Helper text displayed on hover |
| **Visibility controls** | Show/hide inputs conditionally |
| **Remote data population** | Populate options via API routes |
| **Image/video upload** | File upload capabilities |
| **Batch processing** | Process multiple items |
| **Lazy evaluation** | Defer execution until needed |

## Output Specification

Outputs are defined through several properties:

| Property | Description |
|----------|-------------|
| **output** | Array of output type identifiers |
| **output_name** | Display names for each output |
| **output_is_list** | Boolean array indicating list-type outputs |
| **output_tooltips** | Helper text for each output |

## Example Node Definition

```json
{
  "name": "MyCustomNode",
  "display_name": "My Custom Node",
  "description": "A custom node that processes images",
  "category": "image/processing",
  "output_node": false,
  "python_module": "custom_nodes.my_node",
  "input": {
    "required": {
      "image": ["IMAGE"],
      "strength": ["FLOAT", {
        "default": 1.0,
        "min": 0.0,
        "max": 2.0,
        "step": 0.1,
        "display": "slider"
      }]
    },
    "optional": {
      "mask": ["MASK"],
      "seed": ["INT", {
        "default": 0,
        "min": 0,
        "max": 2147483647
      }]
    }
  },
  "output": ["IMAGE"],
  "output_name": ["Processed Image"],
  "output_is_list": [false],
  "output_tooltips": ["The processed output image"]
}
```

## Input Type Details

### Numeric Types (INT, FLOAT)

```json
{
  "value": ["INT", {
    "default": 10,
    "min": 0,
    "max": 100,
    "step": 1,
    "display": "number"
  }]
}
```

Display options:
- `number`: Standard number input field
- `slider`: Slider control
- `knob`: Rotary knob control

### Boolean Type

```json
{
  "enabled": ["BOOLEAN", {
    "default": true,
    "label_on": "Enabled",
    "label_off": "Disabled"
  }]
}
```

### String Type

```json
{
  "prompt": ["STRING", {
    "default": "",
    "multiline": true,
    "placeholder": "Enter your prompt here..."
  }]
}
```

### Combo Type (Dropdown)

```json
{
  "method": [["option1", "option2", "option3"], {
    "default": "option1"
  }]
}
```

### Custom Type References

```json
{
  "model": ["MODEL"],
  "clip": ["CLIP"],
  "vae": ["VAE"],
  "conditioning": ["CONDITIONING"],
  "latent": ["LATENT"],
  "image": ["IMAGE"],
  "mask": ["MASK"]
}
```

## Common Built-in Types

| Type | Description |
|------|-------------|
| `MODEL` | A loaded model checkpoint |
| `CLIP` | CLIP text encoder |
| `VAE` | Variational Autoencoder |
| `CONDITIONING` | Conditioning/prompt embeddings |
| `LATENT` | Latent image representation |
| `IMAGE` | Decoded image tensor |
| `MASK` | Binary or grayscale mask |

## Hidden Inputs

Hidden inputs are used for internal parameters:

```json
{
  "hidden": {
    "node_id": "UNIQUE_ID",
    "prompt": "PROMPT",
    "extra_pnginfo": "EXTRA_PNGINFO"
  }
}
```

## Remote Data Population

For dynamic options fetched from an API:

```json
{
  "model_name": ["STRING", {
    "comfy.api.route": "/api/models",
    "comfy.api.field": "name"
  }]
}
```

## File Upload Inputs

For image or video uploads:

```json
{
  "image": ["IMAGE", {
    "image_upload": true
  }],
  "video": ["VIDEO", {
    "video_upload": true
  }]
}
```

## Lazy Evaluation

For inputs that should be evaluated lazily:

```json
{
  "conditional_input": ["IMAGE", {
    "lazy": true
  }]
}
```
