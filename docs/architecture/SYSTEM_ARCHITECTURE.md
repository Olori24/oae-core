# OAE System Architecture Specification (SAS)

Version: 1.0
Status: Draft

---

# Purpose

The Open Autonomous Engineer (OAE) is an AI Engineering Operating System.

Its purpose is to coordinate autonomous engineering work safely, transparently, and under human governance.

---

# Core Layers

## Layer 0 — Kernel

The kernel provides the fundamental runtime.

Components:

- Runtime
- Memory
- Scheduler
- Registry
- Message Bus
- Security Kernel

No engineering work executes without the kernel.

---

## Layer 1 — Engineering Services

Components:

- Planner
- Builder
- Executor
- Verifier
- Repository Scanner
- Git Intelligence

These services perform engineering tasks.

---

## Layer 2 — Governance

Components:

- Policy Engine
- Approval Engine
- Audit
- Permissions
- Secrets
- Sandbox

Governance protects repositories and users.

---

## Layer 3 — Interfaces

Interfaces include:

- CLI
- API
- IDE Plugins
- MCP
- Future Web UI

Interfaces never bypass governance.

---

# Engineering Flow

Human Mission

↓

Planner

↓

Mission Queue

↓

Scheduler

↓

Builder

↓

Verifier

↓

Security Kernel

↓

Approval Engine

↓

Git

↓

Engineering Ledger

---

# Design Principles

- Security First
- Verification Required
- Human Authority
- Architecture Before Implementation
- One Responsibility Per Module

---

# Long-Term Objective

OAE shall become a trusted engineering operating system capable of coordinating autonomous engineering across hundreds of repositories while remaining secure, explainable, and human-governed.
