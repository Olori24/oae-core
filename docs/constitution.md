# OAE Constitution

Version: 1.0

Status: Active

## Purpose

The OAE Constitution defines the permanent engineering principles that govern every autonomous action performed by OAE.

These principles override implementation details.

---

# Principle 1 — Security First

No repository modification shall occur without passing through the Security Kernel.

---

# Principle 2 — Verification Required

Every engineering action that changes a repository must be verified before completion.

---

# Principle 3 — Repository Safety

Every write operation must be recoverable.

Snapshots shall exist before destructive operations.

---

# Principle 4 — Single Source of Truth

Shared engineering state shall exist in one authoritative location.

Duplicate state is prohibited.

---

# Principle 5 — Modular Architecture

Subsystems communicate through stable interfaces.

No subsystem may bypass another subsystem's public contract.

---

# Principle 6 — Governance Before Automation

Autonomous behavior must always remain observable, auditable and reversible.

---

# Principle 7 — Test Before Commit

Every architectural milestone must pass automated tests before being committed.

---

# Principle 8 — Architecture Before Features

Interfaces and architecture are designed before implementation.
