# Mission 109: Autonomous Action Execution

Mission 109 closes the gap between OAE's durable agent state machine and the existing governed engineering primitives.

## Autonomous loop

1. A bounded engineering plan is persisted.
2. A durable agent run is created.
3. The worker claims exactly one dependency-satisfied action with a short lease.
4. The action is mapped to an existing governed operation.
5. Evidence is persisted.
6. A follow-up durable job advances the run.
7. Verification failures enter a bounded repair/reverification cycle.
8. The run stops on completion, blocked policy, or exhausted repair budget.

## Safety boundary

The autonomous executor does not expose a generic command runner. It can select only the existing allowlisted engineering operations.

Mutation requires an explicit mutation specification in the plan and supports only:
- write
- delete
- branch

No arbitrary shell command, Python expression, URL, or Git ref can be introduced through an agent plan.

## Crash and concurrency behavior

Agent actions use a database lease. A second worker cannot claim a live action. A stale lease can be reclaimed after its bounded expiry.

Completion requires the matching action token, so a stale worker cannot overwrite a newer state transition.

GitHub synchronization remains separately protected by stale-base detection and PR deduplication.

## Repair behavior

Verification and reverification failures can reopen the repair step, but only until the plan's bounded repair budget is exhausted.

OAE never treats a failed verification as a successful build.

## Current limitation

The deterministic planner does not invent source-code patches from a natural-language objective. A mutation input must be supplied by an approved planning layer. This is intentional: adding an unconstrained code-generation model directly to the mutation boundary would bypass the governance architecture.

The next major layer is the model-assisted planning/coding brain, which must produce structured mutation proposals that pass the same policy boundary before execution.
