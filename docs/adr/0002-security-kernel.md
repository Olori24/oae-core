# ADR-0002: Security Kernel

Status: Accepted

Date: 2026-08-03

## Context

Autonomous engineering requires governance before execution.

Without centralized authorization,
every subsystem would implement security independently.

## Decision

Create a Security Kernel responsible for:

- Authorization
- Policies
- Permissions
- Human Approval
- Audit

Every privileged engineering action must pass through the Security Kernel.

## Consequences

Positive:

- Centralized governance
- Consistent authorization
- Easier compliance
- Improved auditability

Negative:

- Additional authorization step
- Slight performance overhead

## Philosophy

Autonomy must never exceed governance.
