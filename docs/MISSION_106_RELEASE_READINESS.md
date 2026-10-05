# Mission 106: CI and Production Readiness Evidence

OAE now separates engineering execution from release readiness.

## CI

GitHubCiInspector reads GitHub check runs for an exact commit SHA and returns
bounded evidence: passed checks, pending checks, failed checks, and an aggregate status.

It is read-only and fail-closed.

## Production gate

evaluate_production_readiness requires all critical evidence before reporting ready.
Deployment and rollback verification are deliberately required for the final production gate.

A successful code verification or PR is therefore not treated as production readiness.

## Deployment constraint

Deployment adapters are intentionally not executed while the current Vercel
deployment quota is exhausted. The gate remains blocked until deployment and
rollback evidence are available.

## Next

Production deployment adapters, health verification, and rollback orchestration
can consume this gate without weakening its fail-closed behavior.
