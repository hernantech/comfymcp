# Workflow Templates in ComfyUI

## Overview

ComfyUI allows custom node developers to showcase example workflows through a template browser system. This feature helps users get started with custom nodes by providing real-world usage examples.

## Implementation

To add workflow templates, create an `example_workflows` folder in your custom node module and place JSON workflow files there. As stated in the documentation: "All you have to do as a node developer is to create an `example_workflows` folder and place the `json` files there."

### Optional Thumbnails

You can enhance template visibility by adding JPG image files with matching names to serve as thumbnails for each workflow.

### Alternative Folder Names

While `example_workflows` is recommended, ComfyUI also accepts these folder names:
- workflow
- workflows
- example
- examples

## Backend Integration

ComfyUI statically serves these files and provides an `/api/workflow_templates` endpoint that returns the complete collection of available templates organized by custom node module.

## Example Structure

For a module called `ComfyUI-MyCustomNodeModule`, the directory structure would be:

```
ComfyUI-MyCustomNodeModule/example_workflows/
├── My_example_workflow_1.json
├── My_example_workflow_1.jpg
└── My_example_workflow_2.json
```

This creates a browsable category in ComfyUI's template browser with two workflow examples, one featuring a thumbnail image.
