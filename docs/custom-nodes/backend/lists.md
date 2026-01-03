# Data Lists - ComfyUI Documentation

## Overview

This documentation page explains how ComfyUI handles data flow between nodes, specifically focusing on list processing mechanisms.

## Key Concepts

### Length One Processing

The Comfy server internally represents data flowing between nodes as Python lists, typically containing a single element of the relevant datatype. The framework automatically wraps outputs into single-element lists and unwraps them when passing data to subsequent nodes.

> "A batch (of, for instance, latents, or images) is a single entry in the list"

This distinction is important: batches are individual entries within lists, not lists themselves.

### List Processing

When workflows process multiple data instances simultaneously, the internal data becomes lists containing multiple elements. Common scenarios include:
- Processing images sequentially to manage VRAM constraints
- Handling images with varying dimensions

By default, Comfy processes list values sequentially with the following behavior:
- Shorter input lists are padded by repeating final values
- The node's main method executes once per list value
- Output lists match the longest input list's length

## Control Attributes

### OUTPUT_IS_LIST

Custom nodes can signal that returned lists should not be wrapped by setting `OUTPUT_IS_LIST` as a tuple of booleans matching `RETURN_TYPES` length.

### INPUT_IS_LIST

Setting `INPUT_IS_LIST = True` allows nodes to receive entire lists in a single call rather than sequential processing. Widget values are then accessed as list elements (e.g., `batch_size[0]`).

The provided `ImageRebatch` example demonstrates this pattern, accepting multiple image batches and reorganizing them into custom-sized batches.
