# Bandit Low-Severity Remediation

## Scope

The post-medium-remediation Bandit inventory contained **47 low-severity findings**: 14 `B404` subprocess-import advisories, 18 `B603` subprocess execution advisories, 14 `B607` partial-executable-path advisories, and one `B112` broad exception continuation. This remediation addresses the actual execution boundary rather than hiding individual findings with scattered suppressions.

## Remediation design

OAE now routes the affected process launches through `src/oae/core/process_security.py`. That single boundary resolves approved executables to absolute, executable local paths; requires existing local working directories; rejects null bytes; constrains Git to approved subcommands; and blocks Git global execution options such as `-c`, `--upload-pack`, `--receive-pack`, and alternate worktree or Git-directory flags. The one narrow Bandit suppression in that module identifies the centralized, validated invocation point rather than suppressing callers that accept unconstrained input.

The Git-specific boundary validates refs, remotes, and HTTPS clone URLs before invoking Git. Clone URLs may not carry credentials, an explicit port, query data, fragments, traversal path components, or an unsupported repository name. Repository clone, checkout, update, materialization, branch, diff, history, status, and manager helpers now use this boundary. Clone and update operations also require an expected local Git worktree before a pull.

The generic repository test runner no longer permits arbitrary executables or arbitrary `python -c` execution. It is restricted to a short local allowlist of Python, pytest, Ruff, and mypy, resolves their executables locally, and returns a non-success result for a rejected request. The engineering-action test path was updated to use the allowed Python version probe instead of treating arbitrary code evaluation as a test operation.

The generated application verifier, frontend build verifier, and workspace materializer were also moved onto the same validated process boundary. The sole `B112` scanner finding was removed by narrowing its silent catch from `Exception` to filesystem and UTF-8 decoding failures only.

## Finding outcome

| Original rule | Original count | Remediation outcome |
|---|---:|---|
| `B404` | 14 | Direct subprocess imports were removed from operational callers. The only retained import is the auditable central process boundary. |
| `B603` | 18 | Direct execution is centralized behind executable, argument, and working-directory validation. |
| `B607` | 14 | Git and approved tool executables are resolved to absolute local paths before execution. |
| `B112` | 1 | The broad scanner catch was replaced with explicit read and decoding failure handling. |

## Validation evidence

The new process-security regression suite covers invalid Git ref syntax, unsupported clone URLs, rejected Git global-option injection, blocked arbitrary Python evaluation, constrained workspace materialization, and unreadable UTF-8 source handling. The relevant focused suites passed **40 tests**, followed by **22** targeted command-policy and engineering-action tests. The final full regression suite passed **889 tests with 4 skipped**. Ruff passed, mypy passed across **328 source files**, `git diff --check` passed, and a fresh Bandit JSON scan reported **0 findings**.

> A zero-finding result applies only to the configured Bandit rules on this source revision. It does not certify the behavior of third-party tools executed within a workspace, a real Git server, a staging host, a compromised local executable, or live production infrastructure.

## Remaining operational boundaries

The process policy intentionally supports only OAE's bounded local quality tools and approved Git operations. New command types must be added through an explicit policy review, executable resolution, operand validation, and test case, not by reintroducing direct subprocess calls. Real-host deployment, worker, Caddy, database, and model-host validation remain separate evidence requirements.
