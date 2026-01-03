# ComfyMCP Integration Test Results

Testing Claude Code's ability to use the ComfyUI MCP server tools.

**Date:** 2026-01-02
**Test Method:** `claude -p --dangerously-skip-permissions "<prompt>"`
**Result:** 13/13 PASSED

---

## Test Battery

| # | Test Name | Prompt | Status | Details |
|---|-----------|--------|--------|---------|
| 1 | check_connection | Use the check_connection tool from comfyui MCP server | PASS | Status: online, URL: http://127.0.0.1:8188 |
| 2 | get_system_stats | Use the get_system_stats tool from comfyui MCP server | PASS | GPU: NVIDIA RTX A5000, VRAM: 23.67GB, PyTorch 2.6.0+cu124 |
| 3 | list_models (types) | Use the list_models tool from comfyui MCP server to list model types | PASS | 21 model types returned |
| 4 | list_models (checkpoints) | Use the list_models tool from comfyui MCP server to list available checkpoints | PASS | 2 checkpoints: sd_turbo.safetensors, sd_xl_turbo_1.0_fp16.safetensors |
| 5 | refresh_nodes | Use the refresh_nodes tool from comfyui MCP server | PASS | 558 nodes loaded, 122 categories |
| 6 | list_nodes (search) | Use the list_nodes tool from comfyui MCP server to search for sampler | PASS | 18 sampler-related nodes found |
| 7 | get_node_info | Use the get_node_info tool from comfyui MCP server to get info about KSampler | PASS | Full node spec: 10 inputs, 1 output (LATENT) |
| 8 | create_workflow | Use the create_workflow tool from comfyui MCP server | PASS | Session ID: d4e10b83-b463-4590-a530-6e6051cdbb45 |
| 9 | get_queue_status | Use the get_queue_status tool from comfyui MCP server | PASS | Queue empty (0 running, 0 pending) |
| 10 | get_history | Use the get_history tool from comfyui MCP server with max_items=3 | PASS | 3 history entries, all success status |
| 11 | Full SD Turbo Workflow | Build 7-node text2img workflow with proper connections, execute | PASS | Generated MCP_Workflow_Test_00001_.png in ~2s |
| 12 | Workflow Validation Errors | Build invalid workflow (KSampler with no inputs), check validation | PASS | Caught 6 missing inputs + 1 warning |
| 13 | Full SDXL Turbo Workflow | Build 7-node 1024x1024 workflow, execute | PASS | Generated SDXL_Test_00001_.png in ~8s |

---

## Detailed Results

### Test 1: check_connection
```
The ComfyUI server is connected and online:
- Status: online
- Server URL: http://127.0.0.1:8188
- Connected: true
```

### Test 2: get_system_stats
```
System Information:
- OS: Linux
- ComfyUI Version: 0.7.0
- Python Version: 3.12.12 (Anaconda)
- PyTorch Version: 2.6.0+cu124
- Total RAM: ~240 GB
- Free RAM: ~232 GB

GPU Device:
- Name: NVIDIA RTX A5000
- Type: CUDA (cuda:0)
- Total VRAM: 23.67 GB
- Free VRAM: 23.38 GB
- Used VRAM: 0.3 GB (1.3%)
```

### Test 3: list_models (types)
```
21 model types available:
checkpoints, configs, loras, vae, text_encoders, diffusion_models,
clip_vision, style_models, embeddings, diffusers, vae_approx,
controlnet, gligen, upscale_models, latent_upscale_models,
custom_nodes, hypernetworks, photomaker, classifiers, model_patches,
audio_encoders
```

### Test 4: list_models (checkpoints)
```
2 checkpoints available:
1. sd_turbo.safetensors
2. sd_xl_turbo_1.0_fp16.safetensors
```

### Test 5: refresh_nodes
```
Node cache refreshed:
- Success: true
- Nodes loaded: 558
- Categories: 122
```

### Test 6: list_nodes (search=sampler)
```
18 sampler-related nodes found including:
- KSampler (sampling)
- KSamplerAdvanced (sampling)
- KSamplerSelect (sampling/custom_sampling/samplers)
- SamplerCustom (sampling/custom_sampling)
- SamplerDPMPP_2M_SDE, SamplerEulerAncestral, etc.
```

### Test 7: get_node_info (KSampler)
```
KSampler node specification:
- Category: sampling
- 10 inputs: model, seed, steps, cfg, sampler_name, scheduler,
             positive, negative, latent_image, denoise
- 1 output: LATENT (slot 0)
- 44 sampler algorithms available
- 9 scheduler options
```

### Test 8: create_workflow
```
New workflow session created:
- Session ID: d4e10b83-b463-4590-a530-6e6051cdbb45
- Status: Successfully created
```

### Test 9: get_queue_status
```
Queue status:
- Running jobs: 0
- Pending jobs: 0
- Total queue length: 0
```

### Test 10: get_history
```
3 recent executions:
1. d85cb60b... - success - ComfyUI_00001_.png
2. 1471658b... - success - ComfyMCP_Test_00001_.png (cached)
3. 5645cbde... - success - No output (fully cached)
```

### Test 11: Full SD Turbo Workflow
```
Built 7-node workflow with connections:
[1] CheckpointLoaderSimple (sd_turbo.safetensors)
 ├── MODEL → [5] KSampler
 ├── CLIP  → [3] CLIPTextEncode (positive)
 │        → [4] CLIPTextEncode (negative)
 └── VAE   → [6] VAEDecode
[2] EmptyLatentImage (512x512) → [5] KSampler
[5] KSampler → [6] VAEDecode → [7] SaveImage

Output: MCP_Workflow_Test_00001_.png
Execution time: ~2 seconds
```

### Test 12: Workflow Validation Errors
```
Invalid KSampler node (no inputs connected):
Errors detected:
- missing_required_input: model
- missing_required_input: sampler_name
- missing_required_input: scheduler
- missing_required_input: positive
- missing_required_input: negative
- missing_required_input: latent_image

Warnings:
- no_output_node: Workflow has no output nodes
```

### Test 13: Full SDXL Turbo Workflow
```
Built 7-node SDXL workflow:
- Checkpoint: sd_xl_turbo_1.0_fp16.safetensors
- Resolution: 1024x1024
- Prompt: "a majestic dragon flying over mountains at sunset"
- Steps: 4, CFG: 1.0, Sampler: euler

Output: SDXL_Test_00001_.png
Execution time: ~8 seconds
```

---

## Summary

All MCP tools are functioning correctly. Claude Code successfully:
- Connected to ComfyUI server
- Retrieved system stats and GPU info
- Listed available models and checkpoints
- Loaded and searched 558 node definitions
- Retrieved detailed node specifications
- Created workflow sessions
- Checked queue status and history
- **Built complete multi-node workflows with proper connections**
- **Validated workflows and caught errors**
- **Executed workflows and generated images**

The ComfyMCP server integration is fully working. Claude Code can:
1. Discover available nodes and their specifications
2. Build sequential workflows connecting node outputs to inputs
3. Validate workflows before execution
4. Queue and monitor workflow execution
5. Generate images with both SD Turbo (512x512) and SDXL Turbo (1024x1024)
