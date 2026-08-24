# Local Open-Source Benchmark: OAE Core

## Scope and evidence boundary

This benchmark was run locally against commit `cd61bfd5e579999c1fa0f8d30f0fb9bbdf1521de` of `https://github.com/Olori24/oae-core.git`. The environment used Python 3.12.3, pytest 9.1.1, Ruff 0.16.4, mypy 1.20.2, pip-audit 2.10.1, Bandit 1.9.4, detect-secrets 1.5.0, and Radon 6.0.1. No repository code was submitted to DataFactor or another source-code evaluation service.

> This is a local code-quality and static-security benchmark. It is **not** a production-readiness, capacity, real-host, dynamic-security, privacy-compliance, or model-quality certification.

## Measured results

| Benchmark area | Tool and command | Measured outcome | Interpretation |
|---|---|---:|---|
| Functional regression | `python3 -m pytest -q --cov=src` | 871 passed, 4 skipped, 1 warning | The full repository suite passed. The skipped tests remain PostgreSQL integration coverage that needs a configured isolated database. |
| Execution time | Shell timing around the coverage run | 134 seconds | Measured on this sandbox only; not a latency or throughput benchmark. |
| Aggregate coverage | pytest-cov terminal report | 75% across all instrumented paths | Includes generated temporary fixtures exercised by tests. It must not be used as the repository-only figure. |
| OAE source coverage | Coverage JSON filtered to `src/oae/` | 81.08%: 4,841 of 5,971 statements across 326 modules | This is the appropriate owned-source coverage figure for this run. |
| Lint | `ruff check src tests scripts` | Passed | Applies the repository’s configured Ruff rule set. |
| Type analysis | `mypy src` | Passed across 327 source files | The configured mypy policy passed; missing third-party imports remain ignored by configuration. |
| Dependency audit | `pip-audit -r requirements.lock.txt -f json` | 0 vulnerabilities among 63 locked packages | The audit completed successfully. It emitted local cache-deserialization warnings, but no known vulnerability was returned. |
| Static security | `bandit -r src -q -f json` | 52 findings: 47 low, 5 medium | Static alerts require contextual triage; they are not confirmed exploitable vulnerabilities. |
| Secret detection | `detect-secrets scan --all-files` with virtual environments and caches excluded | 11 potential matches in 7 tracked files | The scan emits detector candidates, not confirmed secrets. No candidate value is recorded in this report. |
| Complexity | `radon cc src -a -s` | 1,224 blocks, average grade A, average complexity 2.30 | The aggregate complexity profile is low. Several individual blocks are grade C and should be reviewed when changed. |
| Maintainability | `radon mi src -s -j` | No C, D, or F ranked module | This is a static maintainability indicator, not an operational reliability result. |

## Security triage queue

Bandit’s five medium-severity findings are static review items: two permitted-scheme URL-opening alerts in `src/oae/api/github.py:59` and `src/oae/core/application_integration_verifier.py:48`, two string-built SQL alerts in `src/oae/api/migrations.py:28` and `:34`, and one string-built SQL alert in `src/oae/api/realtime_events.py:156`. Their rule identifiers are `B310` and `B608`. The next engineering review should verify that URL scheme, host, redirect, and size limits are enforced for every remote fetch; it should also verify that the dynamic SQL fragments are constrained to trusted identifiers or replaced with safe composition primitives.

The low-severity Bandit findings are predominantly subprocess and shell-command advisories (`B404`, `B603`, and `B607`) plus one try-except-pass advisory (`B112`). They remain useful review signals around command construction, but this benchmark does not label them vulnerabilities without execution-path and input-origin analysis.

The scoped secret scan reported metadata-only candidates in `.github/workflows/ci.yml`, `README.md`, `docs/BETA_DEVELOPER_GUIDE.md`, `src/oae/api/ui.py`, `tests/conftest.py`, `tests/test_staging_validation_scripts.py`, and `tests/test_workspace_models.py`. The candidate detector types were `Secret Keyword` and `Basic Auth Credentials`. The next review should create an approved baseline only after checking each candidate and should preserve a hard failure for newly introduced, unreviewed candidates.

## Coverage and maintainability follow-up

The source-only coverage figure is stronger than the all-instrumented aggregate because the latter includes generated fixture applications under temporary directories. The coverage report nevertheless identifies real OAE modules with no exercised lines. The highest-priority coverage candidates are the runtime-facing agent modules, UI adapters, executor modules, and unsupported core helpers. Before broadening test counts, prioritize modules reachable from public API or worker paths and cover denial, timeout, tenant-isolation, malformed-input, and failure-recovery cases.

Radon identified the following high-complexity blocks for focused future refactoring or branch-level tests: `src/oae/api/github.py::analyze` at 17, `src/oae/core/repository_context.py::analyze` at 15, `src/oae/core/execution_engine.py::execute` and `src/oae/core/engineering_memory.py::decision_effectiveness` at 14, and several blocks at 12 to 13. The benchmark does not prescribe refactoring merely to lower a metric; the priority is retaining explicit policy and failure behavior while testing the branches that justify this complexity.

## Reproduction commands

Run the commands below from the repository root. Store the reports outside the working tree or in an ignored artifact directory, because detector outputs can contain sensitive metadata.

```bash
python3 -m pytest -q --cov=src --cov-report=term-missing --cov-report=json:/tmp/oae-coverage.json
ruff check src tests scripts
mypy src
bandit -r src -q -f json -o /tmp/oae-bandit.json
detect-secrets scan --all-files \
  --exclude-files '^(\.git|\.venv|\.mypy_cache|\.pytest_cache|\.ruff_cache|sandbox|workspace)/' \
  > /tmp/oae-detect-secrets.json
pip-audit -r requirements.lock.txt -f json -o /tmp/oae-pip-audit.json
radon cc src -a -s
radon mi src -s -j
```

## Remaining unmeasured areas

This local run did not test a real PostgreSQL deployment, Caddy or TLS behavior, durable worker and outbox behavior on a real host, distributed rate limiting, backup restoration, external attack simulation, dependency provenance beyond the locked package inventory, load capacity, or the private Ollama model-host smoke test. Those areas remain governed by their existing host-validation and model-host procedures.
