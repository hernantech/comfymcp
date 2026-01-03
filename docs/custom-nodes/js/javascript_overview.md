# Javascript Extensions - ComfyUI Documentation

## Overview

ComfyUI allows developers to extend the client interface through a JavaScript extensions mechanism. The process involves three main steps:

1. **Export `WEB_DIRECTORY`** from your Python module
2. **Place `.js` files** in that directory
3. **Register the extension** using `app.registerExtension`

## Exporting WEB_DIRECTORY

Create a subdirectory (conventionally named `js`) in your custom node folder. Your `__init__.py` should include:

```python
WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
```

## Including JavaScript Files

All `.js` files in the `WEB_DIRECTORY` load automatically when the Comfy webpage loads—no explicit file specification needed. Other resources like CSS files can be accessed at `extensions/custom_node_subfolder/the_file.css` and added programmatically through your JavaScript code.

**Important:** The path does not include the subfolder name; the `WEB_DIRECTORY` value is inserted by the server.

## Registering an Extension

Import the Comfy `app` object and call `app.registerExtension` with a configuration object containing:
- A unique `name` identifier
- One or more hook functions for execution

Example structure:

```javascript
import { app } from "../../scripts/app.js";
app.registerExtension({
  name: "a.unique.name.for.a.useless.extension",
  async setup() {
    alert("Setup complete!")
  },
})
```

## Next Steps

After implementing basic extensions, explore available hooks, Comfy objects, or review example code snippets.
