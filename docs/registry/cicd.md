# Custom Node CI/CD - ComfyUI Documentation

## Overview

The documentation addresses continuous integration/deployment for custom nodes in ComfyUI, recognizing that "When making changes to custom nodes, it's not uncommon to break things in Comfy or other custom nodes."

## Key Components

**Comfy-Action Tool**
The primary solution mentioned is Comfy-Action, which "allows you to run a Comfy workflow.json file on Github Actions. It supports downloading models, custom nodes, and runs on Linux/Mac/Windows."

**CI/CD Dashboard**
Testing outputs are uploaded to the CI/CD Dashboard (ci.comfy.org), enabling developers to review results before publishing or committing changes.

## Purpose

This approach addresses the practical challenge of testing custom node changes across multiple operating systems and PyTorch configurations without local access to every environment combination.
