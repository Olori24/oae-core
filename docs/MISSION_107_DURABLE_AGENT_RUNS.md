# Mission 107: Durable Autonomous Engineering Runs

Mission 107 adds persistent state around OAE's bounded agent controller.

## What changed

- deterministic run-state transition rules
- tenant-scoped PostgreSQL persistence for agent runs
- idempotent run creation
- row-locked step transitions
- bounded repair budget
- bounded evidence retention and evidence size
- durable run start and step-recording jobs
- engineering API endpoints for starting a run and recording a step result

## Control boundary

The run state machine does not execute shell commands, mutate repositories, call GitHub, or invoke a model. It records and advances decisions produced by the existing allowlisted planner/controller.

Consequential work remains behind the existing durable job and worker-authorization boundary.

## Lifecycle

plan -> start run -> select action -> execute governed action -> record evidence -> next action -> verify -> repair if needed -> reverify -> commit -> sync -> PR

A duplicate successful step result is idempotent. A conflicting duplicate result is rejected. A terminal run cannot be mutated.

## Failure behavior

Verification failure can enter the bounded repair path only when the plan contains an optional repair step and the repair budget remains. If the budget is exhausted, the run becomes failed.

The system never promotes a failed or incomplete run to production readiness.

## Persistence

Migration: 0010_engineering_agent_runs.sql

Stored evidence is tenant-scoped and bounded. The database is the source of truth for run state; worker leases remain the source of truth for individual job execution.

## Remaining work

Mission 107 intentionally does not pretend that a persisted state machine is an AI implementation engine. The next layer must safely connect approved agent decisions to concrete governed actions, including repository mutation, verification, repair, GitHub synchronization, CI evidence, and eventually deployment adapters.
