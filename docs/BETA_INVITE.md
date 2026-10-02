# OAE Developer Beta — Invitation

## Message to testers

You're invited to test **OAE — Open Autonomous Engineer**, an engineering system built to help developers understand repositories, run controlled engineering missions, and verify results.

This is an early developer beta. I am looking for practical feedback from people who actually build software.

## Start here

**OAE production workspace:** https://oae-core.vercel.app

### Your first test

1. Open the OAE production workspace.
2. Create a workspace or sign in with an existing API key.
3. If creating a workspace, copy and securely save the one-time API key, then continue.
4. From **Overview**, enter a public GitHub repository URL and select **Analyze repository**.
5. Open **Missions** to follow its status and inspect the repository facts and full result.
6. Open **Analyzed repositories** to see completed snapshots.
7. Refresh the page and confirm the mission history remains available.
8. Sign out and sign back in with your API key.
9. Run another analysis.

You should be able to complete the entire process without anyone walking you through it.

## What I want from you

Tell me where the product:

- confused you
- failed
- felt slow
- produced an unclear result
- gave you information you did not trust
- made something harder than it should be

Screenshots, mission IDs, endpoint names, and exact error messages are especially useful.

When reporting a problem, include:

```text
Device / browser:
Repository tested:
What I expected:
What happened:
Mission ID (if available):
Severity: blocked / serious / annoying / cosmetic
```

## Important

Use **public GitHub repositories only** during this beta unless the OAE team explicitly tells you that private-repository testing is enabled for you.

Never share your OAE API key publicly. It is a secret credential. The key is shown once when the workspace is created.

## The point of this beta

We're not testing whether an AI can generate impressive text.

We're testing whether OAE can become a dependable engineering control system:

```text
Understand
   ↓
Diagnose
   ↓
Plan
   ↓
Authorize
   ↓
Execute
   ↓
Verify
   ↓
Record
```

Your honest feedback is more valuable than a polite "looks good."
