# ComfyUI Custom Nodes: Overview

## Purpose
Custom nodes enable developers to implement new features and share them with the ComfyUI community. They follow a simple pattern: accept input, process it, and produce output.

## Architecture Model

ComfyUI operates on a **client-server architecture**:

- **Server (Python)**: Handles data processing, model management, and image generation
- **Client (JavaScript)**: Manages the user interface
- **API Mode**: Allows non-Comfy clients to send workflows to the server

## Four Categories of Custom Nodes

### 1. Server-Side Only
"The majority of Custom Nodes run purely on the server side, by defining a Python class that specifies the input and output types, and provides a function that can be called to process inputs and produce an output."

### 2. Client-Side Only
Modify the client UI without adding core functionality. May not add new nodes to the system.

### 3. Independent Client and Server
Provide both server features and related UI components (such as widgets for new data types). Communication typically flows through Comfy's data control system.

### 4. Connected Client and Server
UI and server components interact directly with each other in specialized cases.

**Important Limitation**: Nodes requiring direct client-server communication are incompatible with API-only usage.

## Example Resources
- cookiecutter-comfy-extension
- ComfyUI-React-Extension-Template
- ComfyUI_frontend_vue_basic
