# OAE Developer Beta Guide

Welcome to the OAE developer beta.

OAE (Open Autonomous Engineer) is an engineering control system for understanding repositories, producing engineering intelligence, and verifying controlled engineering work. The beta is deliberately focused on one question:

> **Can a developer use OAE successfully without the founder sitting beside them?**

This guide is the complete first-run path.

## 1. Start your workspace

1. Open the OAE production URL.
2. Select **Launch workspace**.
3. Enter your team or developer name.
4. Create the workspace.
5. Copy the one-time API key immediately.
6. Select **Enter workspace**.

The API key is shown once. OAE stores a hash of the key, not the plaintext key.

If you close the dialog before saving the key, create a new workspace/API key rather than trying to recover the old secret.

## 2. Your first mission

From Mission Control:

1. Stay on **Overview**.
2. Paste a public GitHub repository URL, for example:
   `https://github.com/psf/requests`
3. Select **Analyze repository**.
4. Wait for the mission to complete.
5. Open **Missions** to inspect the complete result.
6. Open **Repositories** to see the repository intelligence summary.

Use a repository you are permitted to inspect. The initial public SaaS workflow is read-only.

## 3. What OAE should return

A successful `analyze` mission should give you useful repository facts such as:

- repository identity
- default branch information
- file count
- Python file count
- test file count
- repository metadata/signals

The result is persisted to your tenant's mission history.

## 4. The three beta operations

The public API intentionally exposes only three operations:

| Operation | What it does | Risk |
| --- | --- | --- |
| `analyze` | Reads a public GitHub repository and produces repository intelligence | Read-only |
| `review` | Reviews a supplied list of findings | Read-only |
| `verify` | Verifies supplied success/check data | Read-only |

Repository mutation, arbitrary shell execution, destructive operations, and unrestricted autonomous writes are **not** exposed through the public beta API.

That boundary is intentional. OAE's philosophy is governed autonomy: understand first, authorize consequential actions, execute in a controlled boundary, verify, and record.

## 5. API quickstart

Your API key is used as a Bearer token.

```bash
export OAE_API_KEY='oae_...'
export OAE_URL='https://YOUR-OAE-DOMAIN'
```

Check authentication:

```bash
curl -sS "$OAE_URL/v1/me" \
  -H "Authorization: Bearer $OAE_API_KEY"
```

Create an analysis mission:

```bash
curl -sS -X POST "$OAE_URL/v1/jobs" \
  -H "Authorization: Bearer $OAE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "analyze",
    "payload": {
      "repository_url": "https://github.com/psf/requests"
    }
  }'
```

The response contains the mission ID. Poll it with:

```bash
curl -sS "$OAE_URL/v1/jobs/JOB_ID" \
  -H "Authorization: Bearer $OAE_API_KEY"
```

Interactive API documentation is available at `/docs` on the production service.

## 6. What to test during the beta

Every developer should complete this checklist:

- [ ] Open the landing page on mobile and desktop.
- [ ] Create a workspace without assistance.
- [ ] Save the one-time API key.
- [ ] Enter Mission Control.
- [ ] Analyze a public GitHub repository.
- [ ] Inspect the completed mission.
- [ ] Refresh the page.
- [ ] Confirm mission history remains available.
- [ ] Sign out.
- [ ] Sign back in with the saved API key.
- [ ] Confirm the same mission history is visible.
- [ ] Open API docs.
- [ ] Call `/v1/me` with the API key.
- [ ] Submit one additional analysis mission.

## 7. What good feedback looks like

Do not only report that something is "good" or "bad". Tell us:

**Context**
- What repository did you use?
- What device/browser were you using?

**Expected**
- What did you expect OAE to do?

**Observed**
- What actually happened?

**Impact**
- Blocked / serious / annoying / cosmetic

**Evidence**
- Screenshot, mission ID, endpoint, or error message.

### Useful feedback examples

> "The workspace creation worked, but I did not understand that the API key was one-time until after I closed the dialog."

> "Analysis completed for `owner/repo`, but the repository summary did not tell me what to do next."

> "Mission 8f... stayed queued for more than five minutes."

These reports are actionable. "It doesn't work" is not.

## 8. Security rules

Never paste your OAE API key into:

- GitHub issues
- public repositories
- screenshots
- Discord/Slack channels
- frontend source code
- shell history that will be committed or shared

Treat the key like a password. If you believe it has been exposed, stop using it and create a replacement workspace/key.

Do not submit private repositories during the public beta unless the OAE team has explicitly enabled and approved that workflow for you.

## 9. If something fails

### `401 Invalid API key`

Confirm that the value is the complete `oae_...` key and that the `Authorization` header is exactly:

```text
Authorization: Bearer oae_...
```

### `404 Job not found`

Make sure the mission ID belongs to the current workspace. OAE intentionally scopes job access to the authenticated tenant.

### Mission becomes `failed`

Open the mission result and report:

- mission ID
- repository URL
- failure message
- approximate time

Do not repeatedly submit the same failing mission without reporting the error first.

### The page looks stale

Refresh the page, then sign out and sign back in. Mission state is persisted server-side; the browser session only holds the API key.

## 10. Beta success criterion

A developer is considered **independently onboarded** when they can complete this sequence without help:

```text
Landing page
    ↓
Create workspace
    ↓
Save API key
    ↓
Mission Control
    ↓
Analyze public repository
    ↓
Inspect result
    ↓
Refresh
    ↓
Sign out
    ↓
Sign back in
    ↓
Find previous mission
    ↓
Run another mission
```

The objective of the first 20 developers is not to produce flattering feedback. It is to expose every place where this sequence breaks, confuses users, or produces an untrustworthy engineering result.

## 11. Product philosophy

OAE is not an unrestricted coding chatbot.

The system is built around a controlled engineering loop:

```text
UNDERSTAND
    ↓
DIAGNOSE
    ↓
PLAN
    ↓
AUTHORIZE
    ↓
EXECUTE
    ↓
VERIFY
    ↓
RECORD
    ↓
RECOVER / CONTINUE
```

The beta intentionally starts with read-only repository intelligence. More powerful engineering actions should only become public when their security, isolation, verification, and recovery guarantees are strong enough for real repositories.
