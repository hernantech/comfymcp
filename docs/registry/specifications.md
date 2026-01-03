# pyproject.toml Specifications

This document describes the `pyproject.toml` configuration file requirements for publishing custom nodes to the ComfyUI Registry.

## Overview

The `pyproject.toml` file contains two primary sections for ComfyUI custom nodes:
- `[project]` - Standard Python project metadata
- `[tool.comfy]` - ComfyUI-specific configuration

## [project] Section

### name (required)

The unique identifier for custom nodes, used in installation commands and registry URLs.

**Constraints:**
- Under 100 characters
- Alphanumeric characters, hyphens, underscores, and periods only
- No consecutive special characters
- Cannot begin with numbers or special characters
- Case-insensitive

**Best practices:** Use short, descriptive names without "ComfyUI" prefix.

```toml
[project]
name = "my-custom-node"
```

### version (required)

Must follow semantic versioning (X.Y.Z):
- X: Major version for breaking changes
- Y: Minor version for backwards-compatible features
- Z: Patch version for bug fixes

```toml
version = "1.0.0"
```

### description (recommended)

A concise explanation of node functionality.

```toml
description = "A custom node that provides image processing capabilities"
```

### license (optional)

Two acceptable formats:

```toml
# File reference
license = { file = "LICENSE" }

# License name
license = { text = "MIT License" }
```

### requires-python (recommended)

Specifies supported Python versions using version constraints.

```toml
requires-python = ">=3.10"
```

### dependencies (optional)

List of pip package dependencies required by your node.

```toml
dependencies = [
    "numpy>=1.20",
    "pillow>=9.0"
]
```

### urls (recommended)

Links to related resources via the `[project.urls]` section.

```toml
[project.urls]
Repository = "https://github.com/username/my-custom-node"
Documentation = "https://example.com/docs"
"Bug Tracker" = "https://github.com/username/my-custom-node/issues"
```

### Frontend Version Compatibility (optional)

The `comfyui-frontend-package` dependency manages compatibility with specific frontend versions when your node uses APIs requiring particular versions.

```toml
dependencies = [
    "comfyui-frontend-package>=1.0.0"
]
```

### classifiers (recommended)

Operating system and GPU accelerator compatibility markers for discoverability.

**Operating System Options:**
- `Operating System :: OS Independent`
- `Operating System :: Microsoft :: Windows`
- `Operating System :: POSIX :: Linux`
- `Operating System :: MacOS`

**GPU Accelerator Options:**
- `Environment :: GPU :: NVIDIA CUDA`
- `Environment :: GPU :: AMD ROCm`
- `Environment :: GPU :: Intel Arc`
- `Environment :: GPU :: Apple Metal`
- `Environment :: GPU :: Huawei Ascend`

```toml
classifiers = [
    "Operating System :: OS Independent",
    "Environment :: GPU :: NVIDIA CUDA"
]
```

## [tool.comfy] Section

### PublisherId (required)

Your unique publisher identifier, typically matching your GitHub username.

```toml
[tool.comfy]
PublisherId = "your-github-username"
```

### DisplayName (optional)

User-friendly display name for the custom node shown in the registry and ComfyUI-Manager.

```toml
DisplayName = "My Custom Node"
```

### Icon (optional)

Node icon image for the registry. Supported formats: SVG, PNG, JPG, or GIF.

**Requirements:**
- Maximum dimensions: 400x400 pixels
- Square aspect ratio recommended
- Must be hosted at a publicly accessible URL

```toml
Icon = "https://example.com/icon.png"
```

### Banner (optional)

Larger promotional image for the registry page. Supported formats: SVG, PNG, JPG, or GIF.

**Requirements:**
- 21:9 aspect ratio
- Must be hosted at a publicly accessible URL

```toml
Banner = "https://example.com/banner.png"
```

### requires-comfyui (optional)

Specifies which version of ComfyUI your node is compatible with.

**Supported operators:** `<`, `>`, `<=`, `>=`, `~=`, `<>`, `!=`

```toml
requires-comfyui = ">=0.2.0"
```

### includes (optional)

Forces inclusion of specific folders in registry packaging. Useful for directories that might be gitignored but are required for the node to function.

```toml
includes = ["models", "data"]
```

## Complete Configuration Example

```toml
[project]
name = "my-custom-node"
version = "1.0.0"
description = "A comprehensive custom node for advanced image processing"
license = { file = "LICENSE" }
requires-python = ">=3.10"
dependencies = [
    "numpy>=1.20",
    "pillow>=9.0",
    "torch>=2.0"
]
classifiers = [
    "Operating System :: OS Independent",
    "Environment :: GPU :: NVIDIA CUDA"
]

[project.urls]
Repository = "https://github.com/username/my-custom-node"
Documentation = "https://example.com/docs"
"Bug Tracker" = "https://github.com/username/my-custom-node/issues"

[tool.comfy]
PublisherId = "your-github-username"
DisplayName = "My Custom Node"
Icon = "https://example.com/icon.png"
Banner = "https://example.com/banner.png"
requires-comfyui = ">=0.2.0"
includes = ["models"]
```

## Additional Notes

### Version Immutability

Once a version is published to the registry, it cannot be modified. This ensures reproducibility for users relying on specific versions. If you need to make changes, you must publish a new version.

### Deprecation

Versions can be deprecated through the Registry website. Deprecated versions display messages encouraging users to upgrade to newer releases.

### Security Review

All published nodes undergo security scanning. Nodes passing these checks receive a verification badge in ComfyUI-Manager. For security standards, see the [Registry Standards](./standards.md) documentation.
