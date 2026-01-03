# ComfyUI Workflow JSON Specification v0.4

> Source: https://docs.comfy.org/specs/workflow_json_0.4

This document describes the JSON format used by ComfyUI to represent workflows. The workflow format defines how nodes are connected and configured to create image generation pipelines.

## Overview

ComfyUI workflows are stored as JSON files that contain:
- Version information
- Node definitions with their configurations
- Links connecting node outputs to inputs
- Metadata such as groups and extra information

## Top-Level Structure

A workflow JSON file has the following top-level properties:

| Property | Type | Description |
| --- | --- | --- |
| `version` | number | The workflow format version (0.4) |
| `nodes` | array | List of node objects |
| `links` | array | List of link connections |
| `groups` | array | Optional grouping of nodes |
| `config` | object | Optional workflow configuration |
| `extra` | object | Optional extra metadata |

## Version

The `version` field indicates the workflow format version. For this specification:

```json
{
  "version": 0.4
}
```

## Nodes

Each node in the `nodes` array represents an operation in the workflow:

```json
{
  "id": 1,
  "type": "KSampler",
  "pos": [400, 200],
  "size": [315, 262],
  "flags": {},
  "order": 5,
  "mode": 0,
  "inputs": [...],
  "outputs": [...],
  "properties": {},
  "widgets_values": [...]
}
```

### Node Properties

| Property | Type | Description |
| --- | --- | --- |
| `id` | number | Unique identifier for the node |
| `type` | string | The node class name (e.g., "KSampler", "CLIPTextEncode") |
| `pos` | array | Position [x, y] on the canvas |
| `size` | array | Dimensions [width, height] of the node |
| `flags` | object | Node flags (collapsed, pinned, etc.) |
| `order` | number | Execution order |
| `mode` | number | Node mode (0=always, 1=on event, 2=never, 3=on trigger, 4=bypass) |
| `inputs` | array | List of input slots |
| `outputs` | array | List of output slots |
| `properties` | object | Node-specific properties |
| `widgets_values` | array | Values for widget inputs |
| `title` | string | Optional custom title |
| `color` | string | Optional background color |
| `bgcolor` | string | Optional node body color |

### Node Modes

| Mode | Value | Description |
| --- | --- | --- |
| Always | 0 | Node always executes |
| On Event | 1 | Node executes on event |
| Never | 2 | Node never executes |
| On Trigger | 3 | Node executes on trigger |
| Bypass | 4 | Node is bypassed (skipped) |

### Input Slots

Each input slot defines a connection point:

```json
{
  "name": "model",
  "type": "MODEL",
  "link": 1,
  "slot_index": 0
}
```

| Property | Type | Description |
| --- | --- | --- |
| `name` | string | The input name |
| `type` | string | The data type expected |
| `link` | number/null | ID of the connected link, or null if unconnected |
| `slot_index` | number | The index of this input slot |

### Output Slots

Each output slot defines a data source:

```json
{
  "name": "MODEL",
  "type": "MODEL",
  "links": [1, 5],
  "slot_index": 0
}
```

| Property | Type | Description |
| --- | --- | --- |
| `name` | string | The output name |
| `type` | string | The data type produced |
| `links` | array | List of link IDs connected to this output |
| `slot_index` | number | The index of this output slot |
| `shape` | number | Optional shape indicator |

## Links

The `links` array defines connections between nodes. Each link is an array:

```json
[link_id, origin_node_id, origin_slot, target_node_id, target_slot, type]
```

| Index | Description |
| --- | --- |
| 0 | Link ID (unique identifier) |
| 1 | Origin node ID (source) |
| 2 | Origin slot index (output slot) |
| 3 | Target node ID (destination) |
| 4 | Target slot index (input slot) |
| 5 | Data type string |

Example:

```json
{
  "links": [
    [1, 4, 0, 3, 0, "MODEL"],
    [2, 6, 0, 3, 1, "CLIP"],
    [3, 7, 0, 3, 2, "VAE"]
  ]
}
```

## Groups

Groups allow visual organization of nodes:

```json
{
  "groups": [
    {
      "title": "Sampling",
      "bounding": [100, 100, 500, 400],
      "color": "#3f789e",
      "font_size": 24,
      "locked": false
    }
  ]
}
```

| Property | Type | Description |
| --- | --- | --- |
| `title` | string | Group name |
| `bounding` | array | [x, y, width, height] of the group box |
| `color` | string | Color of the group header |
| `font_size` | number | Title font size |
| `locked` | boolean | Whether the group is locked |

## Widget Values

The `widgets_values` array stores the values of widget inputs (not connected via links). These are stored in order corresponding to the node's widget definitions:

```json
{
  "widgets_values": [
    156680208700286,
    "randomize",
    20,
    8,
    "euler",
    "normal",
    1
  ]
}
```

The order and types depend on the specific node type.

## Common Data Types

| Type | Description |
| --- | --- |
| `MODEL` | A loaded model checkpoint |
| `CLIP` | CLIP text encoder |
| `VAE` | Variational Autoencoder |
| `CONDITIONING` | Prompt conditioning/embeddings |
| `LATENT` | Latent space image representation |
| `IMAGE` | Decoded RGB image tensor |
| `MASK` | Binary or grayscale mask |
| `INT` | Integer value |
| `FLOAT` | Floating point value |
| `STRING` | Text string |
| `COMBO` | Selection from options |
| `BOOLEAN` | True/false value |

## Extra Metadata

The `extra` field can contain additional workflow metadata:

```json
{
  "extra": {
    "ds": {
      "scale": 1,
      "offset": [0, 0]
    },
    "workflow_meta": {
      "created": "2024-01-15T10:30:00Z",
      "modified": "2024-01-15T11:45:00Z",
      "author": "username"
    }
  }
}
```

Common extra properties:
- `ds`: Display settings (scale, offset for canvas view)
- `workflow_meta`: Optional workflow metadata

## Complete Example

```json
{
  "version": 0.4,
  "nodes": [
    {
      "id": 3,
      "type": "KSampler",
      "pos": [863, 186],
      "size": [315, 262],
      "flags": {},
      "order": 5,
      "mode": 0,
      "inputs": [
        {"name": "model", "type": "MODEL", "link": 1},
        {"name": "positive", "type": "CONDITIONING", "link": 4},
        {"name": "negative", "type": "CONDITIONING", "link": 6},
        {"name": "latent_image", "type": "LATENT", "link": 2}
      ],
      "outputs": [
        {"name": "LATENT", "type": "LATENT", "links": [7], "slot_index": 0}
      ],
      "properties": {"Node name for S&R": "KSampler"},
      "widgets_values": [156680208700286, "randomize", 20, 8, "euler", "normal", 1]
    },
    {
      "id": 4,
      "type": "CheckpointLoaderSimple",
      "pos": [26, 474],
      "size": [315, 98],
      "flags": {},
      "order": 0,
      "mode": 0,
      "outputs": [
        {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
        {"name": "CLIP", "type": "CLIP", "links": [3, 5], "slot_index": 1},
        {"name": "VAE", "type": "VAE", "links": [8], "slot_index": 2}
      ],
      "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
      "widgets_values": ["v1-5-pruned-emaonly.ckpt"]
    }
  ],
  "links": [
    [1, 4, 0, 3, 0, "MODEL"],
    [2, 5, 0, 3, 3, "LATENT"],
    [3, 4, 1, 6, 0, "CLIP"],
    [4, 6, 0, 3, 1, "CONDITIONING"]
  ],
  "groups": [],
  "config": {},
  "extra": {
    "ds": {
      "scale": 1,
      "offset": [0, 0]
    }
  }
}
```

## API Format vs Workflow Format

ComfyUI uses two JSON formats:

1. **Workflow Format** (this specification): Contains visual layout, widget values, and is saved/loaded by the UI
2. **API Format**: A simplified format used for execution via the API, containing only the data needed to run the workflow

The API format maps node IDs to their configurations without positional data:

```json
{
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 156680208700286,
      "steps": 20,
      "cfg": 8,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1,
      "model": ["4", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["5", 0]
    }
  }
}
```

## Validation

A valid workflow must:

1. Have a `version` field matching the specification version
2. Contain a `nodes` array with at least one node
3. Have unique node IDs
4. Have valid links referencing existing nodes and slots
5. Have matching data types for connected inputs/outputs

## Version History

Version 0.4 introduces several improvements:
- Better node versioning support
- Enhanced metadata storage in the `extra` field
- Improved link type handling
- Standardized widget value serialization
- Enhanced node mode support
- Improved group functionality

## Backward Compatibility

Version 0.4 maintains backward compatibility with:
- Version 0.3 workflows
- Legacy node definitions
- Existing link formats

## Migration Notes

When upgrading workflows:
1. Node versions are added automatically
2. Extra metadata is preserved
3. Links maintain their original format
