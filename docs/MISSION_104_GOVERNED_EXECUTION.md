# Mission 104: Governed Execution and Verification

Mission 104 gives OAE a controlled way to execute repository quality commands against the same workspace it mutates.

## Execution contract

OAE does not accept arbitrary shell commands.

Commands are selected from an explicit allowlist:

- `python_compile`
- `pytest`
- `ruff`
- `mypy`

The execution boundary:

- never invokes a shell
- resolves executables explicitly
- runs only inside a tenant-approved workspace
- applies command-specific timeouts
- caps captured output
- returns exit-code evidence
- never places credentials into the process environment

## Verification

`POST /v1/engineering/workspaces/verify` executes a bounded sequence and stops on the first failed check.

The evidence records:

- commands requested
- commands actually executed
- exit codes
- pass/fail state
- timeout policy
- bounded output
- workspace identity

A failed check is never reported as verified.

## Lifecycle

```text
workspace
  ↓
mutate
  ↓
commit
  ↓
verify
  ├── compile
  ├── lint
  ├── typecheck
  └── tests
  ↓
sync
  ↓
pull request
```

Mission 105 will add the planning and agent-control layer above these primitives.
