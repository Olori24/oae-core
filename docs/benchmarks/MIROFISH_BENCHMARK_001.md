# MIROFISH-BENCHMARK-001 — Autonomous Simulation Benchmark

## Purpose

Benchmark OAE's ability to understand, audit, reproduce, and stress-test the core capability demonstrated by 666ghj/MiroFish:

seed material → ontology → knowledge graph → agent population → temporal multi-agent simulation → intervention → evidence retrieval → report/interrogation.

This is an engineering benchmark, not a claim that MiroFish provides scientifically calibrated prediction.

## Source snapshot

- MiroFish: `666ghj/MiroFish`
- Observation branch: `main`
- Observation date: 2026-09-28
- OAE benchmark branch: `mission/mirofish-benchmark-001`
- OAE starting revision: `1a4839a7f01bdf97213a34b3c820107a5612987b`
- Reproducibility requirement: before execution, record the exact MiroFish commit SHA and environment manifest. Do not mix observations from different commits.

The MiroFish README describes five stages: graph building, environment setup, simulation, report generation, and deep interaction. Its documented simulation engine is OASIS-based. OAE must verify implementation claims against source rather than treating README claims as evidence.

## Rules

1. Read source before proposing architecture.
2. Record source evidence for every material architectural claim.
3. Do not copy MiroFish implementation into OAE.
4. Separate source facts, measurements, hypotheses, and recommendations.
5. Do not equate agent population with concurrent LLM calls.
6. Every capacity result must include workload definition and environment.
7. A green test means executed evidence, not theoretical capability.
8. Failed experiments are retained as benchmark evidence.
9. Licensing must be reviewed before any reuse of AGPL-covered implementation or dependencies.
10. No political, real-person targeting, or sensitive-persona scenario is required for this benchmark.

## Gates

### G1 — Repository understanding
Produce:
- pipeline map
- service/module map
- external dependency map
- data-flow map
- state-machine map

### G2 — Concurrency and state
Identify:
- process/thread/async boundaries
- queues or IPC
- persistent state
- retry/recovery paths
- simulation lifecycle
- report lifecycle
- likely contention points

### G3 — Capacity model
Model:
- population size
- active agents per round
- rounds
- actions per active agent
- LLM calls per action
- token/context growth
- graph operations
- storage growth

Do not infer concurrency from population size.

### G4 — Adversarial understanding
OAE must explicitly reject or qualify:
- "MiroFish is just a chatbot with personas."
- "5,000 agents means 5,000 simultaneous LLM calls."
- "The graph is only RAG."
- "The final report is simply a transcript summary."

Each rejection must cite repository evidence.

### G5 — Independent reproduction
Build a minimal independent simulation kernel with:
- seed ingestion
- ontology representation
- graph representation
- agent state
- deterministic event scheduler
- intervention injection
- evidence extraction
- report artifact

The reproduction must not copy MiroFish source.

### G6 — Stress series
Run:
100 → 250 → 500 → 1,000 → 2,500 → 5,000 simulated agents.

Record:
- wall time
- active agents/round
- LLM requests
- token counts where available
- peak RAM
- CPU
- graph nodes/edges
- storage
- failures
- retries
- recovered jobs
- report latency

### G7 — NSOS counterfactual
Use the synthetic school scenario in `docs/benchmarks/MIROFISH_NSOS_SCENARIO.md`.

Run identical baseline populations under:
A. launch without structured onboarding
B. launch with WhatsApp onboarding, teacher training, and parent tutorials

Compare trajectories without declaring a political/evaluative winner. This is a software/product simulation benchmark.

### G8 — Evidence report
Produce a machine-readable and human-readable report containing:
- exact source revision
- environment
- workload
- measurements
- failures
- recovery events
- architecture findings
- reproduction findings
- licensing notes
- unresolved questions

## Acceptance criteria

The mission is complete only when:
- all applicable gates have executed;
- every green claim has evidence;
- failures are recorded rather than hidden;
- capacity numbers are reproducible from a declared workload;
- the independent reproduction runs;
- NSOS scenario runs are repeatable;
- no MiroFish implementation is copied into OAE;
- final conclusions distinguish measured facts from architectural inference.

## Output layout

```
artifacts/benchmarks/mirofish-001/
  source-manifest.json
  architecture.md
  dependency-graph.json
  state-machines.md
  concurrency.md
  capacity-model.md
  adversarial-findings.md
  reproduction/
  stress-results.json
  nsos-results.json
  evidence-index.json
  final-report.md
```
