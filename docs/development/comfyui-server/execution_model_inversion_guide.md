# Execution Model Inversion Guide

> Source: https://docs.comfy.org/development/comfyui-server/execution_model_inversion_guide

This document explains the execution model inversion pattern used in ComfyUI for advanced workflow control.

## Overview

ComfyUI's execution model processes nodes in a graph-based order. The execution model inversion allows nodes to have more control over when and how they execute within the workflow.

## Key Concepts

### Graph Execution Order

Nodes are executed based on their dependencies:
1. Nodes without dependencies execute first
2. Downstream nodes wait for their inputs
3. The graph is traversed until all nodes complete

### Execution Caching

ComfyUI caches node outputs when:
- Input values haven't changed
- The node is marked as deterministic
- Previous execution was successful

### Inversion Pattern

The inversion pattern allows nodes to:
- Control execution timing
- Implement conditional logic
- Create loops and iterations

## Implementation

Custom nodes can influence execution through:

1. **Lazy Evaluation**: Defer input processing until needed
2. **Node Expansion**: Replace nodes with subgraphs at runtime
3. **Control Flow**: Implement branching and iteration

## Best Practices

- Use lazy evaluation for optional inputs
- Cache expensive computations
- Handle errors gracefully to avoid graph failures
