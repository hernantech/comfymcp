# Server Overview - ComfyUI

## Overview

The Comfy server is built on the "aiohttp framework" which leverages "asyncio" for asynchronous operations.

### Communication Architecture

**Server to Client:** The server transmits socket messages using the `send_sync` method of the `PromptServer` instance (defined in `server.py`). A socket event listener in `api.js` processes these messages. Refer to the messages documentation for details.

**Client to Server:** The client uses the `api.fetchApi()` method (defined in `api.js`) to send HTTP requests. The server handles these through defined HTTP routes. See the routes documentation for more information.

### Important Workflow Behavior

When you submit a workflow request, the entire workflow—including all widget values—is transmitted to the server. The server does not receive subsequent modifications made after queuing. To alter server behavior during execution, you'll need to implement routes that can process real-time requests.
