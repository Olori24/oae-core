# Bandit Medium-Severity Remediation

- [x] Review the two URL-opening findings for scheme, host, redirect, and response-boundary enforcement.
- [x] Review the three dynamic-SQL findings for trusted-identifier constraints and parameter-safe composition.
- [x] Add focused regressions for rejected URL and SQL-boundary inputs.
- [x] Re-run Bandit, targeted tests, and the full OAE quality suite.
- [x] Document confirmed risk, remediations, residual limits, and verified results.
- [ ] Separately triage the remaining 47 low-severity Bandit findings around subprocess construction and exception handling.
