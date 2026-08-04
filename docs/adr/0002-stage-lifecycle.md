# ADR-0001: Standard Stage Lifecycle

## Status

Accepted

## Context

Pipeline stages originally exposed only an `execute()` method. This made lifecycle behavior inconsistent and duplicated execution logic in the pipeline.

## Decision

Introduce a common `Stage` base class implementing:

- before_execute()
- execute()
- after_execute()
- run()

The `run()` method becomes the only public entry point for stage execution.

## Consequences

- Consistent execution lifecycle
- Reduced code duplication
- Centralized lifecycle management
- Future support for metrics, retries, tracing and monitoring
