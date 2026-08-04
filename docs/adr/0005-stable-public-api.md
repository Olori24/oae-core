# ADR 0005 — Stable Public API

## Status

Accepted

## Context

As OAE evolves, internal implementations will change frequently.
Subsystems may be refactored, replaced, or split into smaller
components.

External callers should not be affected by these changes.

## Decision

OAE exposes stable public interfaces.

Internal implementation details may evolve without requiring changes
to external callers.

The Kernel acts as the primary public entry point.

Examples include:

- initialize()
- shutdown()
- ready()
- health()
- status()
- validate_dependencies()

These interfaces should remain backward compatible whenever possible.

## Consequences

Benefits:

- Easier refactoring
- Better maintainability
- Reduced breaking changes
- Cleaner architecture
- Better plugin support
- Stable SDK surface

Costs:

- Additional wrapper methods may be required.
- Internal refactors must preserve public behavior.

## Principles

- Public APIs are contracts.
- Internal code is implementation.
- Favor compatibility over convenience.
- Breaking changes require a documented ADR and version increment.
