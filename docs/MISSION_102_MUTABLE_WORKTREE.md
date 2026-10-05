# Mission 102: Mutable Repository Worktree

Mission 102 adds the first real change loop inside an OAE workspace.

```text
pinned revision
      ↓
source workspace
      ↓
attach disposable Git metadata
      ↓
branch
      ↓
file mutation
      ↓
diff
      ↓
commit
```

## Governed operations

The engineering API exposes these durable operations:

- `attach`
- `branch`
- `write`
- `delete`
- `diff`
- `commit`

Every operation runs through the existing tenant-scoped worker authorization and durable job system.

## Safety boundaries

- Workspace paths are resolved and must remain below the configured workspace root.
- `.git` cannot be targeted by file mutation.
- Branch names are validated before Git operations.
- Remote repository URLs are validated by the existing process-security policy.
- Mutated file size is bounded.
- Diff evidence is bounded.
- Commits use an explicit OAE automation identity.
- No unrestricted shell endpoint is exposed.

## Important architecture decision

The workspace itself remains disposable. Git metadata is reconstructed only when a governed worktree operation needs it. This keeps the original source snapshot clean while giving OAE a controlled mutation surface.

## Next

Mission 103 should add change-set persistence and GitHub branch/commit/PR synchronization so a local engineering result becomes a reviewable remote change.
