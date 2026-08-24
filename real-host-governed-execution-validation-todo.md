# Real-Host Governed Execution Validation

- [x] Confirm persistent-host access, Docker and Caddy availability, staging DNS, firewall, PostgreSQL, and secret configuration. This sandbox has no Docker runtime, no configured staging-host connection or deployment secrets, and only a local Caddy binary. It cannot provide real-host DNS, firewall, PostgreSQL, worker, relay, or telemetry evidence.
- [x] Add a non-secret host preflight command that checks required tools, Compose configuration, required variable names, repository revision, DNS, and private-port exposure without printing secret values.
- [x] Add a redacted telemetry collection command and report template for gateway, API, worker, relay, migrations, PostgreSQL, and trace-linked validation events.
- [x] Validate the host-ready assets in the sandbox only to the extent possible, recording unavailable Docker and host services as UNKNOWN rather than PASS.
- [ ] Apply staging migrations and validate separate owner, operator, and approver principal roles.
- [ ] Exercise authorization request, self-approval denial, approval, revocation, build-worker enforcement, cursor pagination, and rate-limit controls.
- [ ] Capture redacted gateway, API, worker, relay, PostgreSQL, and authorization-event telemetry with trace identifiers.
- [ ] Analyze evidence, record pass or fail per control, and preserve unambiguous real-host limitations.
