# Low-Severity Bandit Remediation

- [x] Recreate or verify the exact OAE source revision and collect the current Bandit JSON inventory.
- [x] Classify all `B404`, `B603`, `B607`, and `B112` findings by command origin, argument validation, execution environment, and failure handling.
- [x] Remediate genuine subprocess command-construction gaps and silent exception suppression without disabling required OAE operations.
- [x] Add targeted regression tests for command allowlists, controlled working directories, and failure visibility.
- [x] Re-run Bandit, focused tests, full regression, lint, type checks, and whitespace validation.
- [x] Document remediation evidence and any explicitly accepted, constrained low-severity residuals.
- [ ] Subject any future command type or externally sourced executable to policy review, operand validation, and focused regression coverage before activation.
