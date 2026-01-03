# Bottom Panel Tabs

The Bottom Panel Tabs API enables ComfyUI extensions to add custom interface components to the bottom panel of the ComfyUI interface. This is useful for features like logging, debugging tools, and other custom UI elements.

## Overview

Custom tabs can be added to the bottom panel of ComfyUI through the extension system. Each tab requires specific configuration properties and a render function to display content.

## Required Properties

Each tab requires three mandatory properties:

| Property | Description |
|----------|-------------|
| `id` | A unique identifier for the tab |
| `title` | The display title shown on the tab |
| `type` | The type designation for the tab |

The `render` function receives a DOM element where you should insert your tab's content.

## Registration Methods

There are several ways to register bottom panel tabs:

### 1. Basic Approach

Register tabs within `registerExtension` with simple HTML content:

```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "MyExtension.BottomPanelTab",
  async setup() {
    app.extensionManager.registerBottomPanelTab({
      id: "my-custom-tab",
      title: "My Tab",
      type: "custom",
      render: (el) => {
        el.innerHTML = "<div>My custom tab content</div>";
      }
    });
  }
});
```

### 2. Interactive Elements

Add buttons and event listeners to trigger ComfyUI actions:

```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "MyExtension.InteractiveTab",
  async setup() {
    app.extensionManager.registerBottomPanelTab({
      id: "interactive-tab",
      title: "Interactive",
      type: "custom",
      render: (el) => {
        const button = document.createElement("button");
        button.textContent = "Click Me";
        button.addEventListener("click", () => {
          // Trigger ComfyUI actions
          console.log("Button clicked!");
        });
        el.appendChild(button);
      }
    });
  }
});
```

### 3. React Integration

Mount React components using ReactDOM for stateful interfaces:

```javascript
import { app } from "../../scripts/app.js";
import { createRoot } from "react-dom/client";

app.registerExtension({
  name: "MyExtension.ReactTab",
  async setup() {
    app.extensionManager.registerBottomPanelTab({
      id: "react-tab",
      title: "React Tab",
      type: "custom",
      render: (el) => {
        const root = createRoot(el);
        root.render(<MyReactComponent />);
      }
    });
  }
});
```

## Alternative Registration

Developers can bypass the extension wrapper using `app.extensionManager.registerBottomPanelTab()` for standalone tab registration:

```javascript
import { app } from "../../scripts/app.js";

// Direct registration without full extension setup
app.extensionManager.registerBottomPanelTab({
  id: "standalone-tab",
  title: "Standalone",
  type: "custom",
  render: (el) => {
    el.innerHTML = "<p>Standalone tab content</p>";
  }
});
```

## Best Practices

1. Use unique, descriptive IDs for your tabs to avoid conflicts with other extensions
2. Clean up any event listeners or resources when the tab is destroyed
3. Consider using React or other frameworks for complex stateful interfaces
4. Keep tab content focused and relevant to your extension's functionality

## Related Documentation

- [JavaScript Extensions Overview](./javascript_extensions.md)
- [Sidebar Tabs](./javascript_sidebar_tabs.md)
- [Dialog API](./javascript_dialog.md)
- [Toast API](./javascript_toast.md)

---

*Source: [ComfyUI Documentation](https://docs.comfy.org/custom-nodes/js/javascript_bottom_panel_tabs)*
