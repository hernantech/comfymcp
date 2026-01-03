# ComfyMCP

Give Claude the ability to generate images with ComfyUI. Just ask for what you want in natural language.

```
You: "Generate an image of a robot painting a sunset"

Claude: I'll create that image for you.
        [builds 7-node workflow, executes it]
        Done! Generated robot_painting_00001.png in 2.3 seconds.
```

## What You Can Ask

Once installed, Claude can handle requests like:

**Image Generation**
- "Generate an image of a cat astronaut floating in space"
- "Create a 1024x1024 fantasy landscape using SDXL"
- "Make a portrait with negative prompt 'blurry, low quality'"

**Model & System Info**
- "What checkpoint models do I have?"
- "Show me the available samplers"
- "What's my GPU memory usage?"

**Workflow Control**
- "Use 30 steps instead of 20 for better quality"
- "Generate 4 variations with different seeds"
- "What's the status of my last generation?"

Claude handles all the complexity—discovering nodes, building connections, validating the workflow, and monitoring execution.

## How It Works

When you ask Claude to generate an image, it builds a complete ComfyUI workflow:

```
[1] CheckpointLoaderSimple ─────────────────────────────┐
     ├── MODEL ──────────────────────────────────────────┤
     ├── CLIP ───┬──→ [3] CLIPTextEncode (positive) ────┤
     │           └──→ [4] CLIPTextEncode (negative) ────┤
     └── VAE ────────────────────────────────────────────┤
                                                         ▼
[2] EmptyLatentImage ──────────────────────────→ [5] KSampler
                                                         │
                                                         ▼
                                                 [6] VAEDecode
                                                         │
                                                         ▼
                                                 [7] SaveImage
```

This happens automatically. Claude:
1. Discovers available nodes and their inputs/outputs
2. Builds the workflow with proper connections
3. Validates everything before execution
4. Queues the job and monitors completion
5. Reports the output filename

## Installation

### Prerequisites

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) running (default: `localhost:8188`)
- [uv](https://docs.astral.sh/uv/) package manager

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Claude Code (CLI)

```bash
claude mcp add comfyui \
  --transport stdio \
  --env COMFYUI_HOST=127.0.0.1 \
  --env COMFYUI_PORT=8188 \
  -- uvx --from git+https://github.com/hernantech/comfymcp comfymcp
```

### Claude Desktop

Add to your config file:
- Linux: `~/.config/claude/claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "comfyui": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/hernantech/comfymcp", "comfymcp"],
      "env": {
        "COMFYUI_HOST": "127.0.0.1",
        "COMFYUI_PORT": "8188"
      }
    }
  }
}
```

### Verify Installation

Ask Claude: *"Check if ComfyUI is connected"*

You should see confirmation that the server is online with GPU info.

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `COMFYUI_HOST` | ComfyUI server address | 127.0.0.1 |
| `COMFYUI_PORT` | ComfyUI server port | 8188 |
| `COMFYUI_API_KEY` | API key (if required) | None |

For remote ComfyUI servers, update the host:
```bash
claude mcp add comfyui \
  --env COMFYUI_HOST=192.168.1.100 \
  ...
```

---

## Reference

### Available MCP Tools

<details>
<summary><strong>Workflow Execution</strong></summary>

| Tool | Description |
|------|-------------|
| `queue_prompt` | Submit a workflow for execution |
| `get_queue_status` | Check running/pending jobs |
| `get_job_status` | Get status of a specific job |
| `get_history` | View execution history |
| `interrupt_execution` | Stop current generation |
| `clear_queue` | Clear pending jobs |

</details>

<details>
<summary><strong>Workflow Building</strong></summary>

| Tool | Description |
|------|-------------|
| `create_workflow` | Start a new workflow session |
| `add_node` | Add a node with inputs |
| `build_workflow` | Finalize and validate |
| `validate_workflow` | Check for errors |
| `list_nodes` | Search available nodes |
| `get_node_info` | Get node specifications |
| `refresh_nodes` | Reload node definitions |

</details>

<details>
<summary><strong>Assets & Models</strong></summary>

| Tool | Description |
|------|-------------|
| `list_models` | List checkpoints, LoRAs, VAEs, etc. |
| `list_embeddings` | List textual inversions |
| `list_output_images` | List generated images |
| `get_image` | Retrieve an image |
| `upload_image` | Upload for img2img |

</details>

<details>
<summary><strong>System</strong></summary>

| Tool | Description |
|------|-------------|
| `check_connection` | Verify ComfyUI is reachable |
| `get_system_stats` | GPU memory, system info |
| `free_memory` | Unload models, clear cache |
| `get_extensions` | List installed extensions |

</details>

### MCP Resources

| URI | Description |
|-----|-------------|
| `comfyui://nodes` | All available nodes |
| `comfyui://nodes/categories` | Node categories |
| `comfyui://nodes/{class_type}` | Specific node definition |
| `comfyui://outputs` | Recent outputs |
| `comfyui://images/{filename}` | Retrieve image |

---

## Python API

For programmatic use outside of MCP:

```python
from comfymcp.workflow import WorkflowBuilder

builder = WorkflowBuilder()

# Nodes return refs with named outputs
checkpoint = builder.add_node("CheckpointLoaderSimple",
    ckpt_name="sd_turbo.safetensors")

latent = builder.add_node("EmptyLatentImage",
    width=512, height=512, batch_size=1)

positive = builder.add_node("CLIPTextEncode",
    clip=checkpoint.CLIP,  # Named output connection
    text="a beautiful sunset")

negative = builder.add_node("CLIPTextEncode",
    clip=checkpoint.CLIP,
    text="ugly, blurry")

sampler = builder.add_node("KSampler",
    model=checkpoint.MODEL,
    positive=positive.CONDITIONING,
    negative=negative.CONDITIONING,
    latent_image=latent.LATENT,
    seed=42, steps=4, cfg=1.0,
    sampler_name="euler", scheduler="normal", denoise=1.0)

decode = builder.add_node("VAEDecode",
    samples=sampler.LATENT,
    vae=checkpoint.VAE)

builder.add_node("SaveImage",
    images=decode.IMAGE,
    filename_prefix="output")

workflow = builder.build()
```

### Templates

```python
from comfymcp.templates import Text2ImgTemplate, Img2ImgTemplate

# Text to image
txt2img = Text2ImgTemplate(
    checkpoint="sd_turbo.safetensors",
    positive_prompt="a majestic mountain",
    negative_prompt="ugly, blurry",
    width=512, height=512,
    steps=4, cfg=1.0
)
workflow = txt2img.build()

# Image to image
img2img = Img2ImgTemplate(
    checkpoint="sd_turbo.safetensors",
    image="input.png",
    positive_prompt="enhance details",
    denoise=0.6
)
workflow = img2img.build()
```

### Direct Client Usage

```python
from comfymcp.client import ComfyUIClient

async with ComfyUIClient(host="127.0.0.1", port=8188) as client:
    # Queue workflow
    result = await client.queue_prompt(workflow)

    # Check status
    history = await client.get_history(prompt_id=result.prompt_id)

    # List models
    checkpoints = await client.get_models("checkpoints")
```

---

## Requirements

- Python 3.10+
- ComfyUI server running
- MCP-compatible client (Claude Code, Claude Desktop, Cursor, etc.)

## License

MIT License - see [LICENSE](LICENSE) for details.
