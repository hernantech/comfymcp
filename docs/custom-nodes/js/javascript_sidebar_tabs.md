# Sidebar Tabs

The Sidebar Tabs API enables ComfyUI extensions to add persistent, accessible custom tabs to the interface sidebar.

## Core Requirements

Each tab needs four essential properties:

| Property | Description |
|----------|-------------|
| `id` | A unique identifier for the tab |
| `icon` | CSS class for the icon to display |
| `title` | The title text shown for the tab |
| `render` | A function that receives a DOM element where you should insert your tab's content |

## Icon Support

The API supports multiple icon libraries:

- **PrimeVue**: `pi pi-[name]`
- **Material Design**: `mdi mdi-[name]`
- **Font Awesome**: `fa-[style] fa-[name]`

## Implementation Approaches

### Vanilla JavaScript

Create DOM elements directly within the render function. You can optionally persist data via localStorage.

```javascript
app.extensionManager.registerSidebarTab({
  id: "my-custom-tab",
  icon: "pi pi-box",
  title: "My Tab",
  render: (container) => {
    const div = document.createElement("div");
    div.textContent = "Hello from my custom tab!";
    container.appendChild(div);
  }
});
```

### React Integration

Mount React components by importing React/ReactDOM libraries and using `ReactDOM.createRoot()` to render components within the sidebar container.

```javascript
import React from "react";
import ReactDOM from "react-dom/client";
import MyComponent from "./MyComponent";

app.extensionManager.registerSidebarTab({
  id: "my-react-tab",
  icon: "mdi mdi-react",
  title: "React Tab",
  render: (container) => {
    const root = ReactDOM.createRoot(container);
    root.render(<MyComponent />);
  }
});
```

### Dynamic Updates

Listen to graph change events through `app.api.addEventListener("graphChanged", callback)` to refresh tab content responsively. Make sure to clean up by removing event listeners when appropriate.

```javascript
app.extensionManager.registerSidebarTab({
  id: "dynamic-tab",
  icon: "pi pi-refresh",
  title: "Dynamic Tab",
  render: (container) => {
    const updateContent = () => {
      container.innerHTML = "";
      // Update content based on current graph state
    };

    app.api.addEventListener("graphChanged", updateContent);
    updateContent();

    // Cleanup when tab is destroyed
    return () => {
      app.api.removeEventListener("graphChanged", updateContent);
    };
  }
});
```

## Real-World Example

The [ComfyUI-Copilot](https://github.com/AIGODLIKE/ComfyUI-Copilot) GitHub project provides a real-world example of React sidebar implementation.

## Source

This documentation is derived from the official ComfyUI documentation at [docs.comfy.org](https://docs.comfy.org/custom-nodes/js/javascript_sidebar_tabs).
