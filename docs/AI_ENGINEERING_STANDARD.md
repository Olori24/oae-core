# AI Engineering Standard

AI is a governed application capability, not an uncontrolled decision-maker.

Controls:
- provider/model abstraction where practical
- versioned prompts and configuration
- structured outputs with schema validation
- deterministic authorization before actions
- human approval for consequential actions
- token/usage/cost tracking
- latency and failure telemetry
- evaluation datasets for important behaviors
- regression tests for critical AI workflows
- safe fallbacks when providers fail

Only minimum required tenant data should enter model context. Secrets and unrelated tenant data must never be exposed to models.