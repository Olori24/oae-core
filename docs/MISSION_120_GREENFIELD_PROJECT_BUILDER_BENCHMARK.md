# Mission 120 — Greenfield Project-Builder Benchmark

## Objective

Measure whether OAE can generate a fresh, inspectable full-stack starter project and report the real verification outcome instead of inferring success from files existing.

## Run

From an installed OAE Core checkout:

```bash
python benchmarks/greenfield_project_builder.py
python benchmarks/greenfield_project_builder.py \
  --workspace /tmp/oae-opportunityhub \
  --output artifacts/greenfield-benchmark.json
```

The target directory must be empty. The runner retains the generated workspace for inspection, emits a JSON report to stdout and optionally to `--output`, and exits with:

- `0`: OAE's verification gate reports verified.
- `2`: generation completed but the verification gate blocked the result.
- `1`: the benchmark could not complete.

## Pass criteria

- A clean workspace receives generated project files.
- The generated project contract passes.
- The application verification engine reports `verified`.
- Every reported verification check passes.
- The report records the workspace, file inventory, elapsed time, blockers, failed checks, and machine-readable acceptance fields.

A blocked run is a useful benchmark result, not a successful build. Do not edit the generated workspace before saving the first report; preserve the original evidence for comparison.

## Scope limits

This benchmark evaluates the greenfield generation and verification slice. It does **not** yet prove that the generated application was deployed, that product-specific workflows are correct, or that a durable job can survive a worker restart and resume exactly once. Those require separate live deployment and interruption/recovery acceptance tests.

## Current next steps

1. Run this benchmark against a clean workspace and retain the report.
2. Fix concrete failed checks and rerun without weakening the quality gate.
3. Add a fault-injected durable-run test that interrupts between generation and verification, then proves resume is idempotent.
4. Use a protected preview deployment to verify the API route and run status end to end before calling the milestone complete.
