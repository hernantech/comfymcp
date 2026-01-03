# ComfyUI CLI Getting Started Guide

## Overview

The `comfy-cli` is a command line tool that simplifies installation and management of ComfyUI. It's available as open source on GitHub.

## Installation

### CLI Setup
Install via pip:
```bash
pip install comfy-cli
```

Or use Homebrew:
```bash
brew tap Comfy-Org/comfy-cli
brew install comfy-org/comfy-cli/comfy-cli
```

Enable shell completion with:
```bash
comfy --install-completion
```

### ComfyUI Installation
Create a Python 3.9+ virtual environment first. Using conda:
```bash
conda create -n comfy-env python=3.11
conda activate comfy-env
```

Or with venv:
```bash
python3 -m venv comfy-env
source comfy-env/bin/activate
```

Then install ComfyUI:
```bash
comfy install
```

**Note:** CUDA or ROCm installation is required separately depending on your GPU.

## Core Commands

**Launch the application:**
```bash
comfy launch
```

**Install custom nodes:**
```bash
comfy node install <NODE_NAME>
```

The tool leverages `cm-cli` for node management (see GitHub documentation for details).

**Download models:**
```bash
comfy model download <url> models/checkpoints
```

## Contributing & Analytics

Contributions are welcome via the GitHub repository. Submit issues or pull requests, and refer to the Dev Guide for technical details.

Usage analytics are enabled by default but can be disabled with:
```bash
comfy tracking disable
comfy tracking enable  # to re-enable
```
