# ADR-0002: Security Kernel

## Status

Accepted

## Context

Repository modification must never occur without governance.

## Decision

Introduce a dedicated Security Kernel responsible for:

- permissions
- approvals
- policies
- audit

All engineering actions pass through the Security Kernel before execution.

## Consequences

- Security by default
- Centralized authorization
- Compliance-ready architecture
- Easier auditing
