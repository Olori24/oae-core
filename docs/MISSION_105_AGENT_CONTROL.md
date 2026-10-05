# Mission 105: Planning and Agent Control

Mission 105 adds the control layer above OAE's governed repository primitives.

## Boundary

The agent is not given an arbitrary shell, arbitrary Python, unrestricted filesystem
access, or unrestricted GitHub mutation. It receives a bounded engineering plan and
may select only actions from the approved action vocabulary.

## Lifecycle

repository signals -> plan -> dependency-aware action -> governed execution ->
verification -> repair -> commit -> GitHub synchronization -> pull request

The planner is deterministic and testable. It can be replaced or augmented by an
LLM planner later, but the resulting plan must still pass the same action-policy
boundary.

## Safety properties

- bounded plan size
- explicit action allowlist
- dependency-aware execution
- fail-closed unknown actions
- no command execution inside the planner
- no credentials inside plan data

## Next

Mission 106: CI/build/security orchestration and evidence aggregation.
