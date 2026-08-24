# Governed Open-Weight Model Integration

- [x] Inspect the current OAE model and agent boundaries, including existing provider abstractions and tenant controls.
- [x] Select a deployment contract for an authorized open-weight inference endpoint without embedding model weights or credentials in the repository.
- [x] Define model allowlisting, tenant-scoped configuration, bounded input and output handling, request timeout, and redacted telemetry rules.
- [x] Implement a disabled-by-default provider foundation with focused tests and documentation.
- [x] Validate the foundation locally without claiming a real model host, benchmark, or production inference result.
- [x] Select the Qwen3 8B profile as the approved candidate for this controlled private-host smoke test; model production approval remains contingent on real-host evidence.
- [x] Add a private Ollama Compose overlay with no public model-service port and an explicit Qwen3 8B allowlist.
- [x] Add a controlled, non-sensitive smoke-test command that captures only redacted metadata and refuses public or unconfigured endpoints.
- [x] Validate the Compose overlay and smoke-test command locally without pulling weights or representing the sandbox as a model host. The command correctly refused execution because inference remains disabled and no model host is connected.
- [ ] On a connected private model host, pull the approved artifact from an authorized source, record its provenance, and run the controlled smoke test with redacted evidence.
