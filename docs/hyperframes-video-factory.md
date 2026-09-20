# OAE + HyperFrames Video Factory

## Objective

Add deterministic, agent-driven video production to OAE without replacing
HyperFrames. HyperFrames is the HTML/CSS/media -> MP4 rendering layer; OAE is
the governed orchestration layer.

HyperFrames is Apache-2.0, supports local rendering, and exposes agent skills
for Codex, Claude Code, Cursor, Gemini CLI and similar coding agents.

## Target pipeline

```
brief
  -> content planner
  -> script + scene plan
  -> brand/frame specification
  -> HyperFrames composition
  -> lint/check/preview
  -> governed render
  -> verification
  -> artifact registry
  -> platform variants
```

## OAE responsibilities

1. Create a video job with an immutable job ID.
2. Validate the brief and required assets.
3. Generate or update an isolated HyperFrames project.
4. Record the exact Git revision and HyperFrames CLI version.
5. Run lint/check before render.
6. Require approval for externally published assets.
7. Render deterministically.
8. Verify that the expected MP4 exists and is non-empty.
9. Store render metadata, hashes, logs and artifact locations.
10. Support idempotent retries and rollback to the last approved composition.

## HyperFrames responsibilities

- HTML-native composition.
- Seekable/frame-safe animation.
- Browser preview.
- Local/CI/AWS rendering.
- FFmpeg encoding and audio mixing.
- Reusable catalog components.

## First production MVP

### Inputs

- `title`
- `objective`
- `script`
- `duration_seconds`
- `aspect_ratio`
- `brand_tokens`
- `media_assets[]`
- `voiceover`
- `music`
- `variants[]`

### Outputs

For each variant:

- source composition
- preview metadata
- MP4
- SHA-256 hash
- render duration
- renderer/tool versions
- validation status
- approval status

### Initial variants

- 1080x1920 — Reels/TikTok/Shorts
- 1920x1080 — YouTube/LinkedIn
- 1080x1080 — square social

## Agent roles

- **Creative Planner:** converts a brief into scenes and beats.
- **Script Agent:** produces narration and on-screen copy.
- **Visual Agent:** writes HyperFrames HTML/CSS/animation.
- **Media Agent:** resolves local assets and records provenance.
- **Render Agent:** runs lint/check/render.
- **Verifier:** checks duration, dimensions, file existence, hash and policy gates.
- **Publisher:** publishes only approved artifacts.

No agent may report completion unless the verifier has a successful receipt.

## Governance

Every render must carry:

- job ID
- parent job ID when derived from a variant
- source Git SHA
- composition hash
- asset manifest hash
- renderer version
- approval state
- output hash

Publishing remains a separate governed action.

## Installation

Inside a video project:

```bash
npx hyperframes init my-video
cd my-video
npx hyperframes preview
npx hyperframes render
```

For agent workflows, install the current HyperFrames skills:

```bash
npx hyperframes skills update
```

OAE should call these workflows rather than inventing a second video DSL.

## Scaling path

Phase 1: local/CI rendering.

Phase 2: queued workers with isolated workspaces.

Phase 3: distributed AWS Lambda rendering where render volume justifies it.

Phase 4: content-variant generation at scale with deduplicated assets and
content-addressed artifacts.

## Non-goals

- Do not fork HyperFrames.
- Do not replace Remotion in existing projects automatically.
- Do not claim that AI-generated media is free.
- Do not publish automatically without the existing OAE approval policy.
