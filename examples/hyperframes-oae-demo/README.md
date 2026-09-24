# OAE + HyperFrames Demo

This is the first concrete composition for the OAE Video Factory.

## Run

Requires Node.js 22+ and FFmpeg.

```bash
npx hyperframes lint
npx hyperframes check
npx hyperframes render --quality draft --output renders/oae-hyperframes-demo.mp4
```

The composition is intentionally small: it visually explains the pipeline itself.

## What this proves

- OAE can own the job and governance layer.
- HyperFrames can own HTML/CSS/animation rendering.
- The same source can be edited and versioned as code.
- The composition is structured for later platform variants.

The demo does not claim that the full autonomous factory is complete. It is the visual proof-of-concept for the integration boundary.
