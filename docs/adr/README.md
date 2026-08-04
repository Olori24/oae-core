# OAE Architecture Decision Records

| ADR | Title | Status |
|------|---------------------------|----------|
| 0001 | Engineering Pipeline      | Accepted |
| 0002 | Stage Lifecycle           | Accepted |
| 0003 | Security Kernel           | Accepted |
| 0004 | Storage Layer             | Accepted |
| 0005 | Stable Public API         | Accepted |

## Purpose

Architecture Decision Records explain **why** OAE is designed the way it is.

Every architectural change must either:

- follow an existing ADR, or
- introduce a new ADR before implementation.

ADRs are part of OAE's governance model.

## Governance Hierarchy

```
Constitution
      ↓
Governance Standards
      ↓
Architecture Decision Records
      ↓
Code
      ↓
Tests
```

## ADR Principles

- ADRs capture architectural decisions, not implementation details.
- Once accepted, an ADR remains part of the project's historical record.
- Breaking an accepted ADR requires a new ADR explaining the rationale.
- Public APIs should remain stable unless a documented breaking change is approved.
- All significant architectural changes should be traceable to an ADR.
