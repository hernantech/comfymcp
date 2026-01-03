# Comfy-CLI Reference

> **Note**: This document was extracted from the ComfyUI documentation at [docs.comfy.org/comfy-cli/reference](https://docs.comfy.org/comfy-cli/reference). The full reference page contains extensive command documentation; this document captures the core commands available.

`comfy-cli` is a command line tool that makes it easier to install and manage ComfyUI.

## Installation

### Install via pip

```bash
pip install comfy-cli
```

### Install via Homebrew

```bash
brew tap Comfy-Org/comfy-cli
brew install comfy-org/comfy-cli/comfy-cli
```

### Enable Shell Completion

```bash
comfy --install-completion
```

Adds shell completion hints for the command-line interface.

---

## Commands Reference

### comfy install

Install ComfyUI.

```bash
comfy install
```

**Description**: Sets up the ComfyUI application. Requires a virtual environment with Python 3.9+.

**Note**: You still need to install CUDA or ROCm depending on your GPU.

---

### comfy launch

Run ComfyUI.

```bash
comfy launch
```

**Description**: Starts the ComfyUI server and application.

---

### comfy node

Manage custom nodes.

#### comfy node install

Install a custom node.

```bash
comfy node install <NODE_NAME>
```

**Arguments**:
- `<NODE_NAME>`: The name of the custom node to install

**Description**: Installs community-developed custom nodes. Uses `cm-cli` under the hood for node management.

---

### comfy model

Manage models.

#### comfy model download

Download a model from a URL.

```bash
comfy model download <url> <destination>
```

**Arguments**:
- `<url>`: The URL to download the model from
- `<destination>`: The destination path (e.g., `models/checkpoints`)

**Example**:
```bash
comfy model download https://example.com/model.safetensors models/checkpoints
```

---

### comfy tracking

Manage usage analytics.

#### comfy tracking disable

Disable usage tracking.

```bash
comfy tracking disable
```

**Description**: Prevents the tool from collecting usage analytics data.

#### comfy tracking enable

Enable usage tracking.

```bash
comfy tracking enable
```

**Description**: Restores analytics collection after disabling it.

---

## Prerequisites

Before using comfy-cli, ensure you have:

1. **Git** - Install from [git-scm.com/downloads](https://git-scm.com/downloads)
2. **Python 3.9+** - Required for virtual environment setup
3. **Virtual Environment** - Either conda or venv

### Setting Up Virtual Environment

**Using Conda**:
```bash
conda create -n comfy-env python=3.11
conda activate comfy-env
```

**Using venv**:
```bash
python3 -m venv comfy-env
source comfy-env/bin/activate
```

---

## Additional Resources

- [Getting Started Guide](https://docs.comfy.org/comfy-cli/getting-started)
- [Troubleshooting](https://docs.comfy.org/comfy-cli/troubleshooting)
- [GitHub Repository](https://github.com/Comfy-Org/comfy-cli)

---

## Getting Help

To see all available commands and options:

```bash
comfy --help
```

For help on a specific command:

```bash
comfy <command> --help
```
