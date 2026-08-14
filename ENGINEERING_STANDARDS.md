# OAE™ Engineering Standards

OAE™ applies its own engineering standard to its own repository. The system must not exempt itself from the governance it expects to enforce elsewhere.

## Core rules

- Security first.
- Human approval for consequential repository changes.
- Verification before completion.
- Preserve repository safety and rollback capability.
- Prefer small, testable vertical slices.
- Reuse existing abstractions before introducing new ones.
- Avoid duplicated domain logic and opaque heuristics.
- Keep deterministic behaviour where practical.
- Unit tests must not depend on hidden network state.
- Every substantive capability requires normal, edge, and failure-path coverage appropriate to its risk.
- Never claim a test count, capability, or production readiness without current evidence.
- Record consequential architectural decisions.

## Autonomous-change gate

An autonomous engineering change is not complete merely because code was generated. Completion requires:

```text
Analyze → Plan → Approve → Implement → Test → Verify → Re-analyze
```

A failed verification gate blocks completion.

## Repository professionalization

When OAE™ operates on another repository, it must preserve the target project's identity and architecture. Professionalization means improving engineering quality, not homogenizing every repository into OAE's structure.

## Security boundary

External systems, credentials, untrusted repository content, generated code, and autonomous execution must be treated as security-sensitive boundaries. Fail closed where safety requires it.

## Evidence standard

Engineering claims must be traceable to repository state, tests, verification output, or documented decisions. When evidence is unavailable, OAE™ must state the uncertainty rather than infer success.
