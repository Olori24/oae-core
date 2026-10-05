# Mission 110: OAE Coding Brain

## Objective

Give OAE Core a real model-assisted coding capability while preserving the existing execution firewall.

The coding brain converts a bounded repository context plus an engineering objective into a structured mutation proposal. It does not execute commands, write files, commit, push, or create pull requests.

## Boundary

objective + workspace -> context assembler -> approved model -> structured proposal -> policy validation -> agent_action_executor -> worktree mutation -> verification / repair

The model is advisory and proposal-producing. The existing governed execution stack remains authoritative.

## Context controls

- maximum 80 files
- maximum 12,000 characters per selected file
- maximum 8,000 context characters
- generated/dependency directories are excluded
- deterministic path ordering

## Proposal controls

- maximum 32 mutations
- write/delete only
- workspace-relative paths
- no traversal or Git metadata targets
- complete replacement content for writes
- maximum 1.5 MB per generated file
- verification commands restricted to the existing governed allowlist

## Provider controls

The model is selected server-side. Tenants cannot select a model or endpoint. Open-weight inference remains disabled by default and uses the existing bounded Ollama gateway when enabled.

A model response is never treated as verification evidence.

## Current limitation

This mission creates the coding brain and proposal boundary. The next execution layer must pass validated proposals through the existing agent_action_executor, then verify and repair them under the existing durable run lease.
