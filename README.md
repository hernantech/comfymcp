# ComfyMCP

MCP server for ComfyUI workflow automation.

## Features

- **Programmatic Workflow Builder** - Type-safe node construction with named outputs
- **Pre-built Templates** - Common workflows (text2img, img2img)
- **MCP Tools** - Queue management, asset operations, system info
- **MCP Resources** - Node definitions, output images

## Installation

```bash
pip install comfymcp
```

Or for development:

```bash
pip install -e .
```

## Quick Start

### As an MCP Server

```bash
# Start the server (connects to ComfyUI at localhost:8188)
comfymcp

# Or specify a different host/port
comfymcp --host 192.168.1.100 --port 8188
```

### Programmatic Usage

```python
from comfymcp import WorkflowBuilder

# Create a workflow builder
builder = WorkflowBuilder()

# Add nodes with named outputs
checkpoint = builder.add_node("CheckpointLoaderSimple",
    ckpt_name="v1-5-pruned.safetensors"
)

empty_latent = builder.add_node("EmptyLatentImage",
    width=512, height=512, batch_size=1
)

positive = builder.add_node("CLIPTextEncode",
    clip=checkpoint.CLIP,
    text="a beautiful landscape"
)

negative = builder.add_node("CLIPTextEncode",
    clip=checkpoint.CLIP,
    text="ugly, blurry"
)

sampler = builder.add_node("KSampler",
    model=checkpoint.MODEL,
    positive=positive.CONDITIONING,
    negative=negative.CONDITIONING,
    latent_image=empty_latent.LATENT,
    seed=42,
    steps=20,
    cfg=7.5,
    sampler_name="euler",
    scheduler="normal",
    denoise=1.0
)

decode = builder.add_node("VAEDecode",
    samples=sampler.LATENT,
    vae=checkpoint.VAE
)

save = builder.add_node("SaveImage",
    images=decode.IMAGE,
    filename_prefix="output"
)

# Build and submit
workflow = builder.build()
```

## MCP Tools

### Workflow Tools
- `queue_prompt` - Submit a workflow for execution
- `get_queue_status` - Get current queue state
- `get_history` - Get execution history
- `clear_queue` - Clear the queue
- `interrupt_execution` - Stop current execution

### Builder Tools
- `list_nodes` - Search available nodes
- `get_node_info` - Get detailed node specification
- `create_workflow` - Initialize a workflow builder
- `add_workflow_node` - Add a node to a workflow
- `validate_workflow` - Validate a workflow before submission

### Asset Tools
- `list_models` - List available models
- `list_output_images` - List generated images
- `get_image` - Retrieve an image
- `upload_image` - Upload an image

### System Tools
- `get_system_stats` - Get hardware/memory info
- `free_memory` - Trigger memory cleanup
- `refresh_nodes` - Refresh node definition cache

## MCP Resources

- `comfyui://nodes` - List all available nodes
- `comfyui://nodes/categories` - List node categories
- `comfyui://nodes/{class_type}` - Get specific node definition
- `comfyui://outputs` - List recent outputs
- `comfyui://outputs/{prompt_id}` - Get outputs from specific execution
- `comfyui://images/{filename}` - Get a specific image

## Templates

### Text to Image

```python
from comfymcp.templates import Text2ImgTemplate

template = Text2ImgTemplate(
    checkpoint="v1-5-pruned.safetensors",
    positive_prompt="a beautiful landscape",
    negative_prompt="ugly, blurry",
    width=512,
    height=512,
    steps=20,
    cfg=7.5,
)

workflow = template.build()
```

### Image to Image

```python
from comfymcp.templates import Img2ImgTemplate

template = Img2ImgTemplate(
    checkpoint="v1-5-pruned.safetensors",
    input_image="input.png",
    positive_prompt="enhance the details",
    denoise=0.7,
)

workflow = template.build()
```

## Requirements

- Python 3.10+
- ComfyUI server running

## License

MIT
