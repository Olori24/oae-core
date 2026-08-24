# Bandit Medium-Severity Remediation

## Scope

This review addresses the five medium-severity findings from the local Bandit scan recorded in the open-source benchmark. The findings consisted of two URL-opening alerts (`B310`) and three dynamic-SQL alerts (`B608`). The changes were deliberately limited to validation, response, and query-composition boundaries; they do not grant model, worker, migration, or tenant authority.

## Finding review and remediation

| Finding | Contextual risk classification | Remediation | Regression evidence |
|---|---|---|---|
| `B310` in `src/oae/api/github.py:59` | The public analyzer already built its API URL from a constrained GitHub repository URL, but its internal fetch helper could be invoked with another URL and followed default redirects. This was a defense-in-depth gap, not proof of an exploitable SSRF path. | The analyzer now accepts only HTTPS `github.com` repository inputs without credentials, port, query, or fragment. Its fetch helper separately permits only HTTPS `api.github.com/repos/...` URLs, disables redirects, requires JSON, and caps responses at 2 MB. | Boundary tests reject query, fragment, and non-GitHub API URLs before any network access. |
| `B310` in `src/oae/core/application_integration_verifier.py:48` | The prior target was a literal local health URL, so caller-controlled SSRF was not present. Bandit cannot prove that from a generic `urlopen` call. | The verifier now uses `http.client.HTTPConnection` only against fixed `127.0.0.1:8765`, requests only `/health`, requires HTTP 200 JSON, and caps the response at 8 KiB. | The focused test asserts the exact loopback method, path, headers, and connection close. |
| `B608` in `src/oae/api/migrations.py:24` and `:28` | The interpolated migration table name was a module constant, not request input. The scanner correctly identified string SQL construction but could not establish identifier provenance. | The fixed ledger statements are now explicit SQL constants. The inserted migration name remains parameterized. | The migration test checks that the ledger executes only fixed statements and keeps `%s` parameter binding for the name. |
| `B608` in `src/oae/api/realtime_events.py:156` | The former table selection used a fixed two-entry map, so arbitrary aggregate types were already rejected. The interpolation nevertheless made a later unsafe expansion easier. | The table map was replaced by a fixed aggregate-type-to-full-query map. No table identifier is interpolated. | The realtime test verifies the fixed workspace query and rejects an aggregate type containing SQL syntax. |

## Verified results

The remediation suite passed `20` focused tests, and the full OAE suite passed **875 tests with 4 skipped**. Ruff passed, mypy passed across **327 source files**, and `git diff --check` passed. A new Bandit run reported **47 low-severity findings and zero medium or high findings**. The remaining findings are `B112`, `B404`, `B603`, and `B607`; they are not resolved by this focused change and require separate contextual review of exception handling and subprocess invocation boundaries.

> Zero remaining medium findings is a result of this Bandit rule set on this revision. It is not a claim that the system has no security risk, no supply-chain risk, or no real-host security work remaining.

## Residual controls

The GitHub analyzer remains read-only and should retain its fixed host, HTTPS-only, no-redirect, response-size, and JSON checks. The local integration verifier is intentionally a loopback-only probe, not a general HTTP client. The PostgreSQL migrations and realtime ownership checks still require their existing tenant-scope and real-host validation paths; static query composition cannot replace those runtime controls.
