# Hidden and Flexible Inputs

This documentation covers advanced input configurations for ComfyUI custom nodes, including hidden inputs for server-side information and flexible input types for custom data handling.

## Hidden Inputs

ComfyUI supports special hidden input types that allow custom nodes to access server-side information without creating client-side widgets. These are specified in the `INPUT_TYPES` dictionary under a `hidden` key.

### Implementation Example

```python
@classmethod
def INPUT_TYPES(s):
    return {
        "required": {...},
        "optional": {...},
        "hidden": {
            "unique_id": "UNIQUE_ID",
            "prompt": "PROMPT",
            "extra_pnginfo": "EXTRA_PNGINFO",
        }
    }
```

### Available Hidden Input Types

#### UNIQUE_ID

UNIQUE_ID is the unique identifier of the node, and matches the `id` property of the node on the client side. This is useful for node-server communications and tracking specific node instances.

#### PROMPT

PROMPT is the complete prompt sent by the client to the server. This enables access to the full execution graph data, allowing nodes to inspect the entire workflow context.

#### EXTRA_PNGINFO

EXTRA_PNGINFO is a dictionary that will be copied into the metadata of any `.png` files saved. Custom nodes can store additional information here for downstream nodes or file saving.

**Note:** This requires ComfyUI to be started without the `disable_metadata` flag.

#### DYNPROMPT

DYNPROMPT is an instance of `comfy_execution.graph.DynamicPrompt`. It differs from `PROMPT` in that it may mutate during the course of execution in response to Node Expansion. This is an advanced option recommended only for specialized use cases like implementing loops.

## Flexible Inputs

### Custom Datatypes

Users can establish custom datatypes by selecting a unique, uppercase string identifier like `CHEESE`. This custom type can then be used in `INPUT_TYPES` and `RETURN_TYPES`, allowing the Comfy client to restrict connections so only matching datatype outputs connect to matching inputs. Custom datatypes can represent any Python object.

Since the Comfy client lacks knowledge of custom types, developers must designate them as inputs rather than widgets using the `forceInput` option:

```python
@classmethod
def INPUT_TYPES(s):
    return {
        "required": { "my_cheese": ("CHEESE", {"forceInput": True}) }
    }
```

### Wildcard Inputs

The asterisk symbol `*` indicates an input accepting connections from any source. As this lacks official backend support, developers can skip type validation by including an `input_types` parameter in their `VALIDATE_INPUTS` function. The node itself must handle and interpret whatever data is received.

```python
@classmethod
def INPUT_TYPES(s):
    return {
        "required": { "anything": ("*", {}) },
    }

@classmethod
def VALIDATE_INPUTS(s, input_types):
    return True
```

### Dynamically Created Inputs

When inputs are generated on the client side, they cannot be predefined in Python code. To receive such data, use an `optional` dictionary employing `ContainsAnyDict()`, which overrides the `__contains__` method to return `True` for any key. This allows Comfy to pass arbitrarily-named data accessible through `**kwargs` in your main method.

```python
class ContainsAnyDict(dict):
    def __contains__(self, key):
        return True

@classmethod
def INPUT_TYPES(s):
    return {
        "required": {},
        "optional": ContainsAnyDict()
    }

def main_method(self, **kwargs):
    # the dynamically created input data will be in the dictionary kwargs
```
