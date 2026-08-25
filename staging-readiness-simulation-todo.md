# Staging Readiness Simulation

- [x] Record the published revision, deployment assets, and available local container runtime state.
- [x] Validate static service topology, private-port exposure, environment contract, Caddy policy, and private model overlay without starting services. Compose and Caddy runtime syntax checks remain UNKNOWN because their binaries are unavailable.
- [x] Run the host preflight in sandbox mode and record unavailable infrastructure as UNKNOWN rather than PASS.
- [x] Run deployment-focused regression tests and collect non-secret validation outputs.
- [x] Produce a PASS, FAIL, and UNKNOWN readiness record with the exact connected-host steps required for real staging validation.
