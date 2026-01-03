# ComfyUI Server Routes

> Source: https://docs.comfy.org/development/comfyui-server/comms_routes

This document covers the HTTP routes available in the ComfyUI server for client-to-server communication.

## Overview

The ComfyUI server exposes various HTTP endpoints that allow clients to interact with the server. Requests are sent using the `api.fetchApi()` method from `api.js`.

## Core Routes

### Queue Management

| Route | Method | Description |
|-------|--------|-------------|
| `/prompt` | POST | Submit a workflow for execution |
| `/queue` | GET | Get current queue status |
| `/queue` | DELETE | Clear the queue |
| `/interrupt` | POST | Interrupt current execution |

### Workflow Operations

| Route | Method | Description |
|-------|--------|-------------|
| `/history` | GET | Get execution history |
| `/history/{prompt_id}` | GET | Get specific execution history |
| `/view` | GET | View generated images |

### System Information

| Route | Method | Description |
|-------|--------|-------------|
| `/system_stats` | GET | Get system statistics |
| `/object_info` | GET | Get available node definitions |
| `/extensions` | GET | List loaded extensions |

### File Operations

| Route | Method | Description |
|-------|--------|-------------|
| `/upload/image` | POST | Upload an image |
| `/upload/mask` | POST | Upload a mask |
| `/view` | GET | Retrieve output images |

## Custom Routes

Custom nodes can register their own HTTP routes using the aiohttp framework:

```python
from aiohttp import web
from server import PromptServer

@PromptServer.instance.routes.get("/my_custom_route")
async def my_handler(request):
    return web.json_response({"status": "ok"})
```

## Client-Side Usage

```javascript
const response = await api.fetchApi('/my_custom_route');
const data = await response.json();
```
