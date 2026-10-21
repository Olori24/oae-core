# Recovery Runbook

Production recovery must be evidenced, rehearsed, and safe.

Required evidence:
- scheduled database backups
- retention policy
- backup integrity verification
- isolated restore rehearsal
- recorded restore duration
- replayable/versioned migrations
- object-storage recovery where applicable
- secrets/config recovery procedure
- post-restore validation
- operational sign-off

Never perform an unverified destructive restore directly against production.