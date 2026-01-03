# Node Expansion Documentation

## Overview

Node expansion is an advanced technique in ComfyUI that allows custom nodes to return a new subgraph of nodes that replaces itself in the graph execution flow.

## Key Concept

As stated in the documentation: *"Node Expansion is a relatively advanced technique that allows nodes to return a new subgraph of nodes that should take its place in the graph."* This capability enables custom nodes to implement loops and other complex control flow patterns.

## Implementation Requirements

Nodes using expansion must return a dictionary containing two specific keys:

1. **`result`** - A tuple of node outputs, which can include both finalized values and node output references
2. **`expand`** - The finalized graph for expansion

## GraphBuilder Usage

The documentation strongly recommends using the `GraphBuilder` class: *"We highly recommend using the GraphBuilder class when creating subgraphs. It isn't mandatory, but it prevents you from making many easy mistakes."*

## Manual Graph Requirements

If not using GraphBuilder, developers must manually ensure:
- Node IDs are globally unique (including across multiple executions)
- Node IDs remain deterministic and consistent between executions

Alternatively, developers can use `GraphBuilder.alloc_prefix()` to generate unique prefixes and `comfy.graph_utils.add_graph_prefix` to update existing graphs.

## Caching Optimization

For efficient subgraph caching, pass object links rather than non-literal inputs like torch tensors. Use the `rawLink` parameter in input additional parameters to facilitate this approach.
