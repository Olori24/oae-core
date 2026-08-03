# ADR-0001: Engineering Pipeline

Status: Accepted

Date: 2026-08-03

## Context

OAE coordinates multiple engineering subsystems including Security,
Builder, Verifier, Git, Memory, and future multi-agent services.

Direct coupling between these services would create a monolithic
architecture that becomes increasingly difficult to maintain.

## Decision

Introduce an Engineering Pipeline responsible only for coordinating
engineering stages.

The Pipeline does not implement engineering logic.

Each subsystem remains responsible for its own domain.

## Consequences

Positive:

- Clear separation of responsibilities
- Easier testing
- Extensible workflow
- Supports stage-based execution
- Compatible with future plugin architecture

Negative:

- Additional abstraction layer
- Slight increase in architectural complexity

## Philosophy

The Pipeline coordinates.

Services perform work.

Kernel services enforce governance.
