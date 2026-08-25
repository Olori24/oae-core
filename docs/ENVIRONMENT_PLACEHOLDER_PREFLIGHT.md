# Environment Placeholder Preflight

## Purpose

`scripts/check_environment_placeholders.py` is the first non-secret gate before handing OAE to a staging-host operator. It evaluates every declared variable in the supplied environment file and every required OAE deployment key. It reports only variable names, a category, `PASS` or `FAIL`, and an explanation. It never prints a configuration value, password, API key, pepper, database URL, or token.

The script is intentionally narrower than `scripts/staging_preflight.py`. Use the placeholder check to verify that the operator has completed the environment contract. Use the staging preflight afterwards to validate stage flags, Compose file presence, the private API-port policy, Docker and Compose availability, public DNS, and the exact deployed revision.

## Host-handoff sequence

Create the host environment file using the repository template and protected host-side secret management. Run the placeholder check before any build, image pull, migration, or service start.

```bash
chmod 600 .env.staging
python3 scripts/check_environment_placeholders.py \
  --env-file .env.staging \
  --report /var/lib/oae-evidence/environment-placeholder-preflight.json
```

The command returns `0` only when every required and declared variable is configured without a recognized placeholder and every `${VARIABLE}` dependency resolves to a configured value. A non-zero status identifies names only. Correct the listed variables on the host; do not copy the environment file or values into chat, logs, tickets, or source control.

Once it passes, execute the full host-mode staging preflight with the deployment revision pinned:

```bash
python3 scripts/staging_preflight.py \
  --env-file .env.staging \
  --stage bootstrap \
  --expected-revision "$(git rev-parse HEAD)" \
  --report /var/lib/oae-evidence/staging-preflight.json
```

## Report contract

| Field | Meaning |
|---|---|
| `environment_file` | The path assessed on the host. |
| `status` | `PASS` only when no variable remains missing, empty, placeholder-valued, or dependent on an unresolved placeholder. |
| `variables[].name` | Variable name only. |
| `variables[].category` | `sensitive`, `database`, `network`, or `runtime`; this categorizes handling, not the value. |
| `variables[].detail` | Non-secret remediation reason. |
| `summary` | Count of passing and failing variables. |

The placeholder detector identifies empty values and the existing repository patterns such as `replace`, `change me`, `example.com`, and angle-bracket template markers. It also detects a derived variable that references an unresolved `${VARIABLE}`. It does not claim that a syntactically non-placeholder secret is strong, correctly stored, authorized, or valid against an external service. Those controls remain part of host-mode preflight and deployment validation.

## References

[1] [OAE staging-readiness simulation](STAGING_READINESS_SIMULATION_2026_08_25.md)

[2] [OAE real-host Phase 2 validation procedure](REAL_HOST_PHASE_2_VALIDATION.md)
