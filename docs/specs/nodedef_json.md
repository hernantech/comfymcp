# Node Definition JSON Specification

> Source: https://docs.comfy.org/specs/nodedef_json

This document describes the JSON schema for ComfyUI node definitions.

## Overview

Node definitions describe the structure, inputs, outputs, and behavior of ComfyUI nodes. This specification is used for:
- Node documentation
- UI generation
- API compatibility
- Workflow validation

## Basic Structure

```json
{
  "name": "NodeClassName",
  "display_name": "Node Display Name",
  "description": "What this node does",
  "category": "category/subcategory",
  "output_node": false,
  "input": {
    "required": {},
    "optional": {},
    "hidden": {}
  },
  "output": [],
  "output_name": [],
  "output_is_list": []
}
```

## Input Types

### Required Inputs

Must be provided for node execution:

```json
{
  "required": {
    "image": ["IMAGE"],
    "strength": ["FLOAT", {
      "default": 1.0,
      "min": 0.0,
      "max": 2.0
    }]
  }
}
```

### Optional Inputs

Can be omitted:

```json
{
  "optional": {
    "mask": ["MASK"]
  }
}
```

### Hidden Inputs

Internal parameters:

```json
{
  "hidden": {
    "node_id": "UNIQUE_ID",
    "prompt": "PROMPT"
  }
}
```

## Output Definition

```json
{
  "output": ["IMAGE", "MASK"],
  "output_name": ["Processed Image", "Generated Mask"],
  "output_is_list": [false, false]
}
```

## Common Types

| Type | Description |
|------|-------------|
| `IMAGE` | Image tensor |
| `MASK` | Mask tensor |
| `LATENT` | Latent representation |
| `MODEL` | Model checkpoint |
| `CLIP` | CLIP encoder |
| `VAE` | VAE model |
| `CONDITIONING` | Conditioning data |
| `INT` | Integer value |
| `FLOAT` | Decimal value |
| `STRING` | Text value |
| `BOOLEAN` | True/false value |
