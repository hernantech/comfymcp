# ComfyUI Custom Node Documentation Guide

## Overview
ComfyUI supports rich markdown documentation for custom nodes that appears in the UI instead of generic descriptions.

## Key Requirements

**If your node already includes parameter tooltips in its definition**, you may not need additional documentation. The system can display this basic information through the node documentation panel directly.

## Setup Instructions

Create the following directory structure:

1. **Create a `docs` folder** inside your `WEB_DIRECTORY`

2. **Add markdown files** named after your nodes (matching keys in `NODE_CLASS_MAPPINGS`):
   - `WEB_DIRECTORY/docs/NodeName.md` — Default fallback documentation
   - `WEB_DIRECTORY/docs/NodeName/en.md` — English version
   - `WEB_DIRECTORY/docs/NodeName/zh.md` — Chinese version
   - Additional locales as needed (e.g., `fr.md`, `de.md`)

The system automatically loads documentation based on user locale, falling back to the base `NodeName.md` if localized versions aren't available.

## Supported Markdown Features

- Standard markdown syntax (headings, lists, code blocks)
- Images: `![alt text](image.png)`
- HTML video elements with permitted attributes:
  - Tags: `<video>` and `<source>`
  - Allowed attributes: `controls`, `autoplay`, `loop`, `muted`, `preload`, `poster`

## Example Directory Structure

```
my-custom-node/
├── web/
│   └── docs/
│       ├── MyNode.md
│       └── MyNode/
│           ├── en.md
│           └── zh.md
```
