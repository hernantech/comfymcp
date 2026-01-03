# ComfyUI Account API Key Integration

This article explains how to use a ComfyUI Account API Key to call paid API nodes in headless mode.

## Overview

Starting from [PR #8041](https://github.com/comfyanonymous/ComfyUI/pull/8041), you can send prompts directly to the Comfy webserver API and have paid API nodes executed. This enables you to create workflows that combine local open-source models, tools from the custom node community, and popular paid models - all orchestrated through a single API call without requiring a specific frontend interface.

This feature transforms ComfyUI into a backend service accessible via command-line tools or custom frontends.

> **Note**: This page describes the ComfyUI Account API Key used for accessing paid API nodes in workflows. This is different from the API Key used for publishing custom nodes to the registry.

## Prerequisites

Before using this feature, you need:

1. **Register an account** on the [ComfyUI Platform](https://platform.comfy.org/login)
2. **Create an API key** through your account settings
3. **Ensure sufficient account credits** to execute paid API nodes

## Python Example

The following example demonstrates how to send a workflow containing API nodes to your local ComfyUI server:

```python
import json
from urllib import request

SERVER_URL = "http://127.0.0.1:8188"

# Example workflow using FluxProUltraImageNode (a paid API node)
workflow_with_api_nodes = """{
  "11": {
    "inputs": {
      "prompt": "Your prompt here",
      "seed": 589991183902375,
      "aspect_ratio": "1:1"
    },
    "class_type": "FluxProUltraImageNode"
  },
  "12": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": ["11", 0]
    },
    "class_type": "SaveImage"
  }
}"""

prompt = json.loads(workflow_with_api_nodes)

# Add the api_key_comfy_org to the payload's extra_data field
payload = {
    "prompt": prompt,
    "extra_data": {
        "api_key_comfy_org": "your-api-key-here"
    }
}

data = json.dumps(payload).encode("utf-8")
req = request.Request(f"{SERVER_URL}/prompt", data=data)
request.urlopen(req)
```

### Key Implementation Details

1. **Prepare your workflow JSON** - Include any API nodes you want to use (like `FluxProUltraImageNode` in the example)
2. **Add authentication** - Include your API key in the `extra_data` field under the key `api_key_comfy_org`
3. **Send to server** - POST the authenticated payload to your ComfyUI server's `/prompt` endpoint

## Use Cases

This integration enables developers to:

- Run ComfyUI as a backend service
- Execute workflows combining local models with paid API services
- Operate through command-line interfaces or custom frontends
- Eliminate the need for ComfyUI's standard web interface

## Related Documentation

- [API Nodes Overview](/tutorials/partner-nodes/overview) - Learn about available paid API nodes
- [Account Management](/interface/user) - Manage your ComfyUI account and API keys
- [Credits](/interface/credits) - Purchase and manage account credits
- [Logging in with an API Key](/interface/user#logging-in-with-an-api-key) - Alternative login methods
