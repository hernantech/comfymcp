# ComfyUI Custom Nodes Lifecycle Documentation

## Overview

The lifecycle documentation explains how ComfyUI loads and recognizes custom nodes during startup.

## Loading Process

"When Comfy starts, it scans the directory `custom_nodes` for Python modules, and attempts to load them."

Custom nodes must export `NODE_CLASS_MAPPINGS` to be recognized as valid node definitions.

## Module Structure

A Python module requires an `__init__.py` file. The system exports whatever appears in the `__all__` attribute defined within this initialization file.

## Required Components

### NODE_CLASS_MAPPINGS
This must be a dictionary that maps unique node identifiers to their corresponding class implementations across the entire ComfyUI installation.

### NODE_DISPLAY_NAME_MAPPINGS (Optional)
This optional mapping connects the same unique identifiers to human-readable display names. "If `NODE_DISPLAY_NAME_MAPPINGS` is not provided, Comfy will use the unique name as the display name."

### WEB_DIRECTORY (Optional)
For client-side code deployment, export the module-relative path containing JavaScript files. The convention places these in a `js` subdirectory. Note: "Only `.js` files will be served; you can't deploy `.css` or other types in this way."

## Example Structure

A minimal `__init__.py` follows this pattern:
```python
from .python_file import MyCustomNode
NODE_CLASS_MAPPINGS = { "My Custom Node" : MyCustomNode }
__all__ = ["NODE_CLASS_MAPPINGS"]
```

## Error Handling

If code contains errors during import, ComfyUI continues operation but reports the module as failed. Check the Python console for diagnostic information.
