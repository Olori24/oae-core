# Provider Adapter Standard

External services must not leak directly into OAE domain logic.

- Define an internal capability contract first.
- Keep credentials in secure environment configuration.
- Normalize provider errors into stable internal errors.
- Capture safe provider/correlation IDs.
- Make mutations idempotent where supported.
- Track usage, latency, failures, and cost.
- Document replacement/exit paths for material dependencies.
- Provider outages must not corrupt core job state.

Applies to AI, storage, messaging, email, GitHub, databases, analytics, and other external systems.