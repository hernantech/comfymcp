# ComfyUI Registry Overview

## What is the Registry?

"The Registry is a public collection of custom nodes that powers ComfyUI-Manager. Developers can publish, version, deprecate, and track metrics related to their custom nodes."

## Key Benefits

The Registry provides three main advantages:

**Node Versioning**
Using semantic versioning, developers can safely manage custom node updates. "The workflow JSON will store the version of the node used, so you can always reliably reproduce your workflows."

**Node Security**
All nodes undergo security scanning for malicious behavior including custom pip wheels and arbitrary system calls. Nodes passing these checks receive a verification flag in ComfyUI-Manager.

**Search Functionality**
Users can search across all Registry nodes to discover existing solutions for their workflows.

## Publishing Custom Nodes

Developers can get started by following the official publishing tutorial. Once published, custom node versions cannot be changed, ensuring stability for users relying on specific versions.

## Node Management

**Versioning**: Custom nodes use semantic versioning to communicate upgrade impacts.

**Deprecation**: Developers can deprecate versions through the Registry website, displaying messages encouraging users to upgrade.

**Identification**: Each node has a globally unique name, enabling Comfy Workflow JSON files to identify nodes without collisions.
