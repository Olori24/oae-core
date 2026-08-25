# OAE Core Security Posture Summary

**Assessment date:** 25 August 2026  
**Repository:** `Olori24/oae-core`  
**Published revision assessed:** `a0cbc7ee8cf3db717b0dff6d30f87e45c899105d`  
**Assessment scope:** Repository source, tests, static analysis, locked Python dependencies, committed CI and deployment configuration, and engineering documentation.

> **Decision boundary.** This is an evidence-backed source and configuration assessment. It does not certify a live staging or production deployment, public TLS, backup restoration, distributed rate limiting, sustained availability, model-host security, or capacity at any user count.

## Executive conclusion

OAE Core has a **controlled-beta security foundation** rather than an unrestricted autonomous-agent runtime. The repository shows materially implemented safeguards for tenant ownership, hashed API keys, principal-role separation, optional governed build authorization, durable PostgreSQL job and outbox primitives, authenticated replayable event delivery, and a private-by-default Compose topology. The current source-level quality and static-security gates are healthy.

The important limitation is operational: the controls that depend on PostgreSQL, Caddy, worker and relay processes, DNS, firewall rules, secrets, storage, and a private model host have not been proven on an actual staging host. Build authorization enforcement and open-weight inference remain deliberately disabled by default. OAE should therefore be described as **repository-hardened and staging-ready**, not production-certified or capacity-proven. [1] [2]

## Current measured evidence

| Evidence area | Current result | Interpretation |
|---|---:|---|
| Full regression suite | **889 passed, 4 skipped, 1 warning** | The four skipped tests require an isolated PostgreSQL integration environment. The remaining warning is FastAPI TestClient deprecation. |
| Current aggregate coverage | **76%**: 5,167 of 6,840 instrumented statements | Includes generated fixture applications and should not be used as OAE-owned source coverage. |
| OAE-owned source coverage | **81.05%**: 4,987 of 6,153 statements across 327 modules | Exceeds the repository’s enforced 70% floor, but does not prove every runtime or operational path. |
| Lint and type checks | Ruff passed; mypy passed across **328 source files** | Confirms the configured static quality policy on the assessed revision. |
| Bandit static security | **0 findings** | All previously reported medium and low findings were contextually remediated and re-scanned. This result applies only to Bandit’s configured rules. [3] [4] |
| Locked dependency audit | **0 known vulnerabilities** across **63** locked packages | A fresh `pip-audit` run completed successfully. This is not a dependency-provenance or runtime-behavior certification. |
| CI supply-chain automation | Dependency audit, full-history secret scan, and pull-request dependency review are configured | The security workflow uses hash-checked locked dependencies and fails dependency review on high severity. [5] |
| Secret-detection follow-up | **11 metadata-only detector candidates** were recorded in an earlier scoped local scan | Candidates were not reported as confirmed secrets. A reviewed baseline or triage record remains outstanding. [6] |

## Security control assessment

The classifications below use the following terms. **Verified in repository** means implemented and supported by tests or static evidence. **Partial** means a meaningful control exists but a material dependency, adversarial scope, or operational proof remains. **Real-host-only** means source configuration exists but it cannot be credibly validated in the ordinary sandbox. **Unknown** means no sufficient evidence exists for a claim.

| Security domain | Classification | Implemented evidence | Material boundary or gap |
|---|---|---|---|
| Tenant isolation | **Verified in repository** | Tenant-scoped repositories, revisions, workspaces, jobs, authorization records, and event ownership checks are covered by API and subsystem regressions. [1] [2] | Every future tenant-owned aggregate still needs adversarial cross-tenant tests. |
| API-key protection | **Verified in repository** | API keys are returned once and stored as PBKDF2 hashes; authentication uses tenant binding and revocation controls. [1] [2] | Key rotation, secret-store integration, usage telemetry, and enterprise identity federation are not proven. |
| Principal separation and governed builds | **Partial** | Owner, operator, approver, and viewer roles exist; requester self-approval is denied; authorization expiry and revocation are represented; worker enforcement is available. [1] [2] | Enforcement is disabled by default and needs separate-principal staging evidence before activation. Scope-policy evaluation remains incomplete. |
| Repository and credential boundaries | **Verified in repository** | Tenant-scoped registry and revision pins reject unsafe clone URLs; database state stores an external `credential_ref`, not plaintext credentials. [1] [2] | Credential-reference resolution and host-side secret handling need a real secret-management workflow. |
| Outbound fetch and SSRF posture | **Partial** | GitHub analysis is restricted to fixed HTTPS GitHub origins, blocks redirects, requires JSON, and enforces response bounds; generated-app health checks are loopback-only. [3] | There is no general egress policy, DNS rebinding test, or network-level outbound allowlist evidence. |
| SQL and persistence boundaries | **Partial** | Tenant query parameters are used; migration ledger and realtime ownership statements were converted to fixed SQL; PostgreSQL durable primitives are implemented. [3] | PostgreSQL integration tests are skipped locally, and live storage, locking, and failure modes need host-backed proof. |
| Local command execution | **Verified in repository** | Process launches pass through one validated boundary that resolves absolute executables, requires existing working directories, restricts Git operations, validates clone inputs, and blocks arbitrary Python evaluation in the test runner. [4] | Third-party commands and tools remain inherently risky; new command types require explicit policy review and runtime sandboxing has not been proven. |
| Durable jobs and outbox | **Partial** | PostgreSQL leases, heartbeats, retry, stale-lease recovery, transactional outbox records, relay leases, and ordered replay records are implemented. [1] [2] | Feature flags, worker processes, migration status, and recovery require real-host validation. |
| SSE and event confidentiality | **Partial** | Authenticated tenant-scoped SSE, replay, cursor expiry, snapshots, and anti-buffering Caddy configuration are present. [1] [2] | Fan-out, slow-consumer isolation, reconnect storms, and capacity are unmeasured. |
| Rate limiting and abuse resistance | **Partial** | Selected control writes have process-local limits and `429` with `Retry-After`. [1] [2] | There is no distributed, shared-store, or edge-enforced rate-limit proof for horizontal deployment. |
| Supply chain and secret hygiene | **Partial** | Hash-pinned dependency install, pip-audit, Gitleaks workflow, and PR dependency review are configured; the current lockfile audit found no known vulnerability. [5] | Detector candidates need documented triage; SBOM/provenance and container-image signing were not verified. |
| Observability and auditability | **Partial** | Request IDs, JSON logging, optional Sentry integration, durable authorization events, and redacted staging-telemetry tooling exist. [1] [2] | No live metric collection, alert routing, trace continuity, dashboard, or SLO measurement is proven. |
| Network and deployment exposure | **Real-host-only** | Compose keeps the API, worker, relay, and database private; Caddy is the intended public edge on ports 80 and 443. [1] [2] | DNS, firewall, TLS issuance, Caddy behavior, secrets, and port exposure have not been exercised on a real host. |
| Backup, restoration, and disaster recovery | **Unknown** | Runbooks and recovery-oriented lifecycle code exist. [1] [2] | No successful backup and restore drill was captured. |
| Open-weight model gateway | **Partial, disabled by default** | Private Ollama adapter restricts operation class, tenant pseudonymized audit metadata, response bounds, and model allowlisting; it has no public model port. [7] | No model is production-approved, no weights were pulled, and no private host smoke test or capacity evidence exists. |

## Bandit and code-quality remediation history

The initial local benchmark recorded five medium and 47 low Bandit findings. The medium findings covered generic URL-opening and dynamically composed SQL patterns. They were remediated with fixed origins, no redirects, bounded JSON responses, fixed loopback health checks, fixed SQL statements, and fixed aggregate ownership queries. [3]

The low findings covered direct subprocess imports, execution of commands, partial executable paths, and one broad exception continuation. The remediation created a central process-security boundary. It resolves approved executables, rejects unsafe Git options and malformed repository inputs, confines the repository test runner to a small local-tool allowlist, and narrows the scanner’s exception handling. The final Bandit JSON scan reported no findings. [4]

This is a meaningful code-hardening result, but a static result is not an authorization to execute arbitrary repository contents. OAE must continue to treat cloned source, package installation, build scripts, test hooks, and external tool behavior as hostile until an execution-isolation design is validated.

## Threat-oriented view

| Threat | Current defensive position | Remaining proof requirement |
|---|---|---|
| Cross-tenant data access | Tenant-bound data access, authentication, and not-found behavior are implemented and regression-tested. | Broaden adversarial tests as new data aggregates and routes are added. |
| API-key disclosure or misuse | One-time return, salted hashing, tenant binding, role keys, and revocation exist. | Establish key rotation, secret-store, audit-review, and compromised-key response procedures. |
| Unauthorized build execution | Optional active authorization, separate approver identity, expiry, revocation, and worker claim checks exist. | Execute the separate-principal approval, denial, revocation, and worker-claim tests on PostgreSQL staging. |
| SSRF or unsafe remote repository interaction | Narrow GitHub API and HTTPS repository URL boundaries are implemented. | Add network egress policy and run adversarial redirect, DNS, and service-discovery tests in staging. |
| Command injection | A central command policy validates executables, working directories, Git options, refs, and test-tool selection. | Verify container or VM isolation, untrusted-repository containment, resource quotas, and host-level least privilege. |
| SQL injection | Parameter binding and fixed SQL composition were strengthened. | Exercise the PostgreSQL path, migration lifecycle, and tenant ownership queries against a live isolated database. |
| Vulnerable dependencies | Hash-locked dependency installation, scheduled audit, and fresh audit result with no known vulnerabilities. | Record provenance/SBOM evidence and maintain timely patch response beyond the audit’s known-vulnerability database. |
| Secret leakage | Environment templates and redaction tooling exist; CI runs history-aware Gitleaks. | Triage the local detector candidates and validate log, error, trace, and host-secret redaction in staging. |
| Event disclosure or replay misuse | Authenticated SSE, tenant scope, replay cursors, and snapshots exist. | Measure fan-out, slow-consumer behavior, relay failures, and connection limits under real load. |

## Priority remediation and validation roadmap

| Priority | Required action | Why it matters | Closure evidence |
|---|---|---|---|
| P0 | Run the governed-execution staging procedure on a persistent private host | Authorization enforcement, durable workers, outbox, relay, and SSE are not proven by source inspection. | Redacted approval, self-approval denial, revocation, worker-claim, event, and health evidence. [8] |
| P0 | Add gateway or shared-store distributed rate limiting before horizontal scale | The present limiter is deliberately process-local. | Verified multi-instance behavior with bounded control writes and consistent `429` handling. |
| P0 | Complete backup and restoration drill | Recovery evidence is absent. | Timestamped restore evidence, data-integrity checks, recovery-time result, and operator sign-off. |
| P1 | Triage the 11 secret-detector candidates and establish a reviewed baseline | Detector candidates should be resolved rather than silently accepted. | Candidate disposition record plus CI failure on novel unreviewed candidates. |
| P1 | Add host-level execution isolation tests for cloned repositories and third-party tools | Static command validation does not isolate malicious project code. | Sandbox, container, VM, network egress, filesystem, and resource-limit test evidence. |
| P1 | Establish operational telemetry, alerts, and SLOs from measured behavior | Repository logging is not a production observability system. | Metrics, dashboards, alert rules, trace samples, and realistic workload baselines. |
| P2 | Validate private model-host activation only after artifact, license, and capacity review | The open-weight gateway is intentionally inert in the current posture. | Private-host smoke-test record, model provenance, access controls, and redacted audit evidence. [7] |
| P2 | Extend identity and policy administration | API-key roles are not enterprise identity governance. | Approved design and tests for rotation, federation, role administration, and policy scope evaluation. |

## Final posture statement

The assessed OAE Core revision has a defensible **repository-level security posture for a controlled beta**. Its strongest verified areas are tenant-scoped control-plane boundaries, role-aware authorization foundations, source-level quality gates, static security remediation, locked dependency auditing, and deliberate limitation of command and model authority.

It is not accurate to claim production hardening is complete. The decisive remaining controls are operational and environment-specific: real-host authorization enforcement, gateway and rate controls, database and worker failure handling, backup restoration, observability, secret handling, execution isolation, and capacity measurement. These should be treated as release gates, not documentation follow-ups.

## References

[1] [OAE README: available controls, authorization, deployment, and quality gates](../README.md)

[2] [Production Platform Mandate Baseline](PRODUCTION_PLATFORM_MANDATE_BASELINE.md)

[3] [Medium-Severity Bandit Remediation Record](BANDIT_MEDIUM_REMEDIATION_2026_08_24.md)

[4] [Low-Severity Bandit Remediation Record](BANDIT_LOW_REMEDIATION_2026_08_24.md)

[5] [GitHub Actions Security Workflow](../.github/workflows/security.yml)

[6] [Local Open-Source Benchmark](LOCAL_OPEN_SOURCE_BENCHMARK_2026_08_24.md)

[7] [Governed Open-Weight Model Gateway](OPEN_WEIGHT_MODEL_GATEWAY.md)

[8] [Real-Host Phase 2 Validation Procedure](REAL_HOST_PHASE_2_VALIDATION.md)
