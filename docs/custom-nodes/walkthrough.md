# Getting Started

This guide walks through creating a custom node that selects images based on various criteria.

## Write a basic node

### Prerequisites

- A working ComfyUI [installation](/installation/manual_install). For development, we recommend installing ComfyUI manually.
- A working comfy-cli [installation](/comfy-cli/getting-started).

### Setting up

Navigate to the custom nodes directory and run the scaffold command:

```bash
cd ComfyUI/custom_nodes
comfy node scaffold
```

This generates a new project directory after you answer configuration prompts. The example demonstrates responses including project name "FirstComfyNode," license selection (GNU General Public License v3), and enabling web directory inclusion for custom JavaScript.

### Defining the node

A custom node in ComfyUI is built using a Python class with four essential components:

**CATEGORY**: This determines the menu location where users will find the node when adding new elements to their workflow.

**INPUT_TYPES**: A class method that defines the parameters the node accepts. It returns a dictionary specifying required inputs and their data types.

**RETURN_TYPES**: Specifies what outputs the node will produce, defined as a tuple of type identifiers.

**FUNCTION**: Names the method that executes when the node runs.

The example implementation:

```python
import torch

class ImageSelector:
    CATEGORY = "example"
    @classmethod
    def INPUT_TYPES(s):
        return { "required":  { "images": ("IMAGE",), } }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "choose_image"
```

> **Important**: The data type for input and output is `IMAGE` (singular) even though we expect to receive a batch of images. In ComfyUI, `IMAGE` means image batch, and a single image is treated as a batch of size 1.

### The main function

The `choose_image` function receives named arguments from `INPUT_TYPES` and returns a tuple matching `RETURN_TYPES`. Since images are handled as `torch.Tensor` objects with shape `[B,H,W,C]` (batch size, height, width, channels), the function iterates through the batch to calculate brightness.

The implementation uses `torch.mean(image.flatten()).item()` to compute average pixel values. When iterating over the tensor, each element has shape `[H,W,C]`. The `.flatten()` method converts it to a single dimension, `torch.mean()` calculates the average, and `.item()` extracts it as a Python float.

```python
def choose_image(self, images):
    brightness = list(torch.mean(image.flatten()).item() for image in images)
    brightest = brightness.index(max(brightness))
    result = images[brightest].unsqueeze(0)
    return (result,)
```

The final steps involve selecting the brightest image and reshaping it. `images[brightest]` will return a Tensor of shape `[H,W,C]`. `unsqueeze` is used to insert a (length 1) dimension at dimension zero, to give us `[B,H,W,C]` with `B=1` - a single-image batch.

> **Note**: The return statement uses `return (result,)` with a trailing comma to ensure proper tuple formatting, which is essential for the node's output handling.

### Register the node

To enable ComfyUI to recognize your custom node, you must make it accessible at the package level by modifying the `NODE_CLASS_MAPPINGS` variable in `src/nodes.py`.

**NODE_CLASS_MAPPINGS**: This dictionary maps internal node identifiers to their corresponding Python classes:

```python
NODE_CLASS_MAPPINGS = {
    "Example" : Example,
    "Image Selector" : ImageSelector,
}
```

The keys are internal names used by the system, while the values reference the actual class definitions.

**NODE_DISPLAY_NAME_MAPPINGS**: This optional dictionary provides user-friendly names that appear in the ComfyUI interface:

```python
NODE_DISPLAY_NAME_MAPPINGS = {
    "Example": "Example Node",
    "Image Selector": "Image Selector",
}
```

The mapping allows you to show more descriptive labels to end users while maintaining simpler internal identifiers.

> **Important**: You must restart ComfyUI to see any changes made to these mappings or node definitions.

## Add some options

You can enhance the ImageSelector node with selection criteria by modifying the `INPUT_TYPES` method to include a "mode" parameter:

```python
@classmethod
def INPUT_TYPES(s):
    return { "required":  { "images": ("IMAGE",),
                            "mode": (["brightest", "reddest", "greenest", "bluest"],)} }
```

The updated `choose_image` function implements different scoring logic based on the selected mode. For "brightest," it uses the mean brightness values. For the color options, it calculates the average value of the relevant color channel divided by the average of all three colors.

```python
def choose_image(self, images, mode):
    batch_size = images.shape[0]
    brightness = list(torch.mean(image.flatten()).item() for image in images)
    if (mode=="brightest"):
        scores = brightness
    else:
        channel = 0 if mode=="reddest" else (1 if mode=="greenest" else 2)
        absolute = list(torch.mean(image[:,:,channel].flatten()).item() for image in images)
        scores = list( absolute[i]/(brightness[i]+1e-8) for i in range(batch_size) )
    best = scores.index(max(scores))
    result = images[best].unsqueeze(0)
    return (result,)
```

The implementation extracts the relevant color channel (0 for red, 1 for green, 2 for blue) and computes relative intensity by dividing that channel's mean by the overall brightness. A small epsilon value (1e-8) prevents division by zero errors. The node then selects and returns the image with the highest score for the chosen mode.

## Tweak the UI

### Send a message from server

To transmit data from the backend to the frontend, import the server module:

```python
from server import PromptServer
```

Then, within the `choose_image` method, send a notification to the frontend:

```python
PromptServer.instance.send_sync("example.imageselector.textmessage", {"message":f"Picked image {best+1}"})
return (result,)
```

This approach allows the node to push updates to connected clients using a unique message identifier and associated data.

### Write a client extension

The frontend component requires creating a JavaScript file in the `web/js` subdirectory and updating `__init__.py` to export `WEB_DIRECTORY`:

```python
WEB_DIRECTORY = "./web/js"
__all__ = ['NODE_CLASS_MAPPINGS', 'WEB_DIRECTORY']
```

The client-side code registers an extension and listens for the server's messages:

```javascript
import { app } from "../../scripts/app.js";
app.registerExtension({
	name: "example.imageselector",
    async setup() {
        function messageHandler(event) { alert(event.detail.message); }
        app.api.addEventListener("example.imageselector.textmessage", messageHandler);
    },
})
```

When the message arrives, the event handler accesses the transmitted data through `event.detail` and performs appropriate UI actions, such as displaying an alert with the selected image information.

### The complete example

The complete example is available on [GitHub Gist](https://gist.github.com/robinjhuang/fbf54b7715091c7b478724fc4dffbd03).

The complete example integrates:
- The `ImageSelector` class with mode selection options
- Server-side messaging using `PromptServer`
- Client-side JavaScript extension registration with event listeners
- Proper registration in `NODE_CLASS_MAPPINGS` and `WEB_DIRECTORY` configuration
