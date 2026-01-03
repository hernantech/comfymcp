# Publishing Nodes to Comfy Registry

This guide covers how to publish custom nodes to the Comfy Registry, which is the public collection of custom nodes that powers ComfyUI-Manager.

## Overview

The ComfyUI Registry is a centralized platform where developers publish custom nodes and users discover them. Key features include:

- **Versioning & Stability**: Uses semantic versioning, allowing users to control upgrades. Once a custom node version is published, it cannot be changed, ensuring reliable workflow reproduction.
- **Security Verification**: All nodes undergo security scanning for malicious behavior. Verified nodes receive a badge in the ComfyUI-Manager interface.
- **Discovery**: Users can search across all published nodes to find solutions for their workflows, with ratings and metrics available for each node.

## Prerequisites

Before publishing, install the comfy-cli by following the getting started guide.

## Setup Steps

### 1. Create a Publisher Account

Visit [Comfy Registry](https://registry.comfy.org) and create a publisher account. Your publisher ID is globally unique and cannot be changed later because it is used in the URL. The publisher ID appears after the `@` symbol on your profile.

### 2. Generate an API Key

Navigate to the registry, select your publisher, and create an API key. This API key is specifically for publishing custom nodes to the Registry and ComfyUI-Manager.

**Important**: Store your API key securely. If lost, you will need to generate a new one - you cannot recover lost keys.

### 3. Initialize Node Metadata

Run the following command to generate a `pyproject.toml` file:

```bash
comfy node init
```

### 4. Configure pyproject.toml

Edit the generated `pyproject.toml` to include your publisher ID, display name, version, and other metadata.

#### Required Fields

**[project] section:**
- `name`: Node identifier (alphanumeric, hyphens, underscores, periods only; max 100 characters; cannot start with a number or special character)
- `version`: Uses semantic versioning (X.Y.Z format)

**[tool.comfy] section:**
- `PublisherId`: Your unique publisher identifier (typically your GitHub username)

#### Recommended Fields

- `description`: Brief explanation of your node's functionality
- `repository`: Link to your project's repository under `[project.urls]`
- `requires-python`: Supported Python versions (e.g., `">=3.8"`)
- `license`: Specify as either `{ file = "LICENSE" }` or `{ text = "MIT License" }`
- `classifiers`: Indicate OS compatibility and GPU accelerator support

#### Optional Fields

- `DisplayName`: User-friendly display name for your node
- `Icon`: Square image URL (max 400x400px) in SVG, PNG, JPG, or GIF format
- `Banner`: Larger promotional image with 21:9 aspect ratio
- `requires-comfyui`: Specify ComfyUI version compatibility using operators like `>=`, `<`, `~=`
- `includes`: Force-include specific folders in the packaged output
- `comfyui-frontend-package`: Dependency constraints to specify required frontend versions

#### Complete Example

```toml
[project]
name = "super-resolution-node"
version = "1.0.0"
description = "Enhance image quality using advanced super resolution techniques"
license = { file = "LICENSE" }
requires-python = ">=3.8"
dependencies = [
    "comfyui-frontend-package<=1.21.6"
]
classifiers = [
    "Operating System :: OS Independent"
]
dynamic = ["dependencies"]

[tool.setuptools.dynamic]
dependencies = {file = ["requirements.txt"]}

[project.urls]
Repository = "https://github.com/username/super-resolution-node"
Documentation = "https://github.com/username/super-resolution-node/wiki"
"Bug Tracker" = "https://github.com/username/super-resolution-node/issues"

[tool.comfy]
PublisherId = "image-wizard"
DisplayName = "Super Resolution Node"
Icon = "https://raw.githubusercontent.com/username/super-resolution-node/main/icon.png"
Banner = "https://raw.githubusercontent.com/username/super-resolution-node/main/banner.png"
requires-comfyui = ">=1.0.0"
```

## Publishing Methods

### Option 1: Manual CLI Publishing

Execute the following command and enter your API key when prompted:

```bash
comfy node publish
```

**Note**: When pasting your API key on Windows, your API key might have an additional `\x16` at the back when using CTRL+V. It is recommended to right-click to paste to avoid hidden characters.

The system will confirm publication with a link to your published node. The node will be accessible at `registry.comfy.org/publisherId/your-node` after publishing.

### Option 2: Automated GitHub Actions

For automated publishing whenever you update your `pyproject.toml` version:

#### Step 1: Store API Key as Repository Secret

1. Go to your repository Settings
2. Navigate to Secrets and Variables > Actions
3. Create a new repository secret named `REGISTRY_ACCESS_TOKEN`
4. Paste your API key as the value

#### Step 2: Create Workflow File

Create a file at `/.github/workflows/publish_action.yml` with the following content:

```yaml
name: Publish to Comfy registry
on:
  workflow_dispatch:
  push:
    branches:
      - main
    paths:
      - "pyproject.toml"

jobs:
  publish-node:
    name: Publish Custom Node to registry
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v4
      - name: Publish Custom Node
        uses: Comfy-Org/publish-node-action@main
        with:
          personal_access_token: ${{ secrets.REGISTRY_ACCESS_TOKEN }}
```

**Note**: If your working branch is named something besides `main`, such as `master`, add the name under the branches section.

#### Step 3: Test the Workflow

Push an update to the version number in your `pyproject.toml` file. The workflow will automatically run and publish your node to the registry.

## Version Management

- **Semantic Versioning**: X.Y.Z format where X indicates major/breaking changes, Y represents new backwards-compatible features, and Z denotes bug fixes
- **Immutable Versions**: Once a custom node version is published, it cannot be changed
- **Deprecation**: Developers can deprecate outdated versions, notifying users to upgrade while maintaining access to stable older releases

## Important Notes

- Publisher IDs are permanent and globally unique
- Each node receives a globally unique identifier, preventing naming collisions in workflow JSON files
- Keep your API key secure and never commit it to your repository
- The workflow automatically re-runs each time you modify and push the `pyproject.toml` file
