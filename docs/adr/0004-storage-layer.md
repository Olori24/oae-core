# ADR-0003: Storage Layer

## Status

Accepted

## Context

Snapshots are not limited to repositories. Future versions of OAE may store mission state, artifacts, policies and backups.

## Decision

Introduce a dedicated `storage` package containing storage-related services, beginning with `SnapshotManager`.

## Consequences

- Clean separation of concerns
- Extensible persistence architecture
- Repository-independent storage abstractions
