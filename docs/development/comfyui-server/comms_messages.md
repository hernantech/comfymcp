# ComfyUI Messages Documentation

## Overview

During execution or when queue state changes, the `PromptExecutor` transmits messages to clients via the `PromptServer.send_sync()` method. A socket event listener in `api.js` receives these messages and dispatches them as `CustomEvent` objects to registered handlers.

Extensions can register listeners using:

```javascript
api.addEventListener(message_type, messageHandler);
```

The message handler receives a `CustomEvent` with a `.detail` property containing the server data.

## Built-in Message Types

| Event | Trigger | Data |
|-------|---------|------|
| `execution_start` | Before prompt runs | `prompt_id` |
| `execution_error` | During execution error | `prompt_id` + additional info |
| `execution_interrupted` | Node raises `InterruptProcessingException` | `prompt_id`, `node_id`, `node_type`, `executed` list |
| `execution_cached` | Start of execution | `prompt_id`, nodes list |
| `execution_success` | All nodes complete | `prompt_id`, `timestamp` |
| `executing` | Node about to execute | `node` (id or None), `prompt_id` |
| `executed` | Node returns UI element | `node` id, `prompt_id`, `output` |
| `progress` | During node execution | `node` id, `prompt_id`, `value`, `max` |
| `status` | Queue state changes | `exec_info` with `queue_remaining` |

## Using the `executed` Message

The `executed` message fires only when nodes return UI updates, not on every completion. Return a dictionary instead of a tuple:

```python
return { "ui": a_new_dictionary, "result": the_tuple_of_output_values }
```

## Custom Messages

**Client-side registration:**
```javascript
api.addEventListener("my.custom.message", messageHandler);
```

**Server-side sending:**
```python
from server import PromptServer
PromptServer.instance.send_sync("my.custom.message", a_dictionary)
```

## Accessing node_id

Include a hidden input in `INPUT_TYPES` to receive the current node's ID:

```python
@classmethod
def INPUT_TYPES(s):
    return {
        "required": {},
        "hidden": { "node_id": "UNIQUE_ID" }
    }

def my_main_function(self, required_inputs, node_id):
    PromptServer.instance.send_sync("my.custom.message",
        {"node": node_id, "other_things": etc})
```
