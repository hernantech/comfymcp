# Commands and Keybindings

The Commands and Keybindings API enables ComfyUI extensions to register custom commands and associate them with keyboard shortcuts. This allows users to quickly trigger actions without using the mouse.

## Overview

Commands are actions that can be triggered programmatically or through user interaction. Keybindings link keyboard combinations to these commands, providing quick access to extension functionality.

## Commands

### Required Properties

Each command requires three essential properties:

| Property | Description |
|----------|-------------|
| `id` | A unique identifier for the command |
| `label` | The display name shown to users |
| `function` | The code that executes when the command is triggered |

### Registering Commands

Use `useCommandStore` to register custom commands:

```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "MyExtension.Commands",
  async setup() {
    const commandStore = app.extensionManager.command;

    commandStore.registerCommand({
      id: "my-extension.my-command",
      label: "My Custom Command",
      function: () => {
        console.log("Command executed!");
        // Your command logic here
      }
    });
  }
});
```

## Keybindings

### Required Properties

Each keybinding requires two essential properties:

| Property | Description |
|----------|-------------|
| `combo` | Object specifying the key and optional modifiers |
| `commandId` | The ID of the command to trigger |

### Combo Object Structure

The `combo` object defines the keyboard combination:

| Property | Type | Description |
|----------|------|-------------|
| `key` | string | The key to press (e.g., "a", "Enter", "F1") |
| `ctrl` | boolean | Whether Ctrl key must be held |
| `shift` | boolean | Whether Shift key must be held |
| `alt` | boolean | Whether Alt key must be held |
| `meta` | boolean | Whether Meta/Command key must be held |

### Registering Keybindings

```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "MyExtension.Keybindings",
  async setup() {
    const keybindingStore = app.extensionManager.keybinding;

    keybindingStore.registerKeybinding({
      combo: {
        key: "k",
        ctrl: true,
        shift: true
      },
      commandId: "my-extension.my-command"
    });
  }
});
```

## Supported Special Keys

The API supports various non-character keys:

### Arrow Keys
- `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`

### Function Keys
- `F1` through `F12`

### Navigation Keys
- `Home`, `End`, `PageUp`, `PageDown`

### Special Keys
- `Escape`, `Tab`, `Enter`, `Backspace`, `Delete`, `Space`

## Complete Example

Here is a complete example registering both a command and its keybinding:

```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "MyExtension.QuickAction",
  async setup() {
    // Register the command
    app.extensionManager.command.registerCommand({
      id: "my-extension.quick-action",
      label: "Quick Action",
      function: () => {
        // Perform the action
        alert("Quick action triggered!");
      }
    });

    // Register the keybinding
    app.extensionManager.keybinding.registerKeybinding({
      combo: {
        key: "q",
        ctrl: true,
        alt: true
      },
      commandId: "my-extension.quick-action"
    });
  }
});
```

## Important Limitations

### Core Keybindings Cannot Be Overwritten

Keybindings defined in the ComfyUI core cannot be overwritten by extensions. Before registering a keybinding, check the existing core keybindings to avoid conflicts.

### Browser-Reserved Combinations

Browser-reserved keyboard combinations cannot be overridden. Common examples include:

- `Ctrl+F` (Find)
- `Ctrl+P` (Print)
- `Ctrl+S` (Save)
- `Ctrl+W` (Close tab)
- `Ctrl+T` (New tab)

### Conflicting Keybindings

Undefined behavior occurs when multiple extensions register identical keybindings. Always use unique, descriptive command IDs and consider prefixing keybindings with your extension name.

## Checking Existing Keybindings

Before implementing custom keybindings, developers should check which keybindings are already reserved in the core system. The ComfyUI frontend repository contains files defining core keybindings and commands.

## Best Practices

1. **Use unique command IDs**: Prefix your command IDs with your extension name (e.g., `my-extension.my-command`)
2. **Choose non-conflicting keybindings**: Avoid common shortcuts and check core bindings first
3. **Provide meaningful labels**: Command labels should clearly describe the action
4. **Document your keybindings**: Let users know what shortcuts your extension provides
5. **Consider accessibility**: Not all users can easily use modifier keys

## Related Documentation

- [JavaScript Extensions Overview](./javascript_overview.md)
- [Comfy Hooks](./javascript_hooks.md)
- [Settings](./javascript_settings.md)
- [Topbar Menu](./javascript_topbar_menu.md)

---

*Source: [ComfyUI Documentation](https://docs.comfy.org/custom-nodes/js/javascript_commands_keybindings)*
