# OAE UX revival plan

## Product direction

OAE is a governed engineering control plane for developers who need repository context and evidence before trusting AI-assisted engineering work. The beta's useful first promise is deliberately narrow: **give a developer a trustworthy, inspectable read on a public GitHub repository, and preserve that result in a workspace**. Do not present a broad autonomous-agent vision as an already shipped user journey.

## Jakob's Law applied

Jakob's Law says people bring expectations from the other sites and products they already use. OAE should therefore reuse established workspace conventions instead of asking a first-time developer to learn a bespoke “command center”:

- A conventional workspace shell: recognizable product header, left navigation, page title, one clear primary action, and a main content area.
- Familiar mission history: scannable rows/cards, explicit lifecycle status, dates, repository identity, and an expandable details area.
- Standard onboarding: create or sign into a workspace; explain the API key before issuance; show the one-time secret with a copy action and a clear continue action.
- Familiar feedback: visible empty, loading, success, and recoverable error states; announce state updates accessibly; never use color alone to communicate status.
- Plain language before internal terminology: “Analyze a repository” first; introduce “mission” as the saved unit of work and “governed control plane” only as supporting context.

The goal is not to copy a particular vendor's visual identity. It is to preserve familiar interaction patterns while making evidence and human authority distinctively OAE.

## Design direction

- **Design movement:** quiet Swiss-inspired engineering workbench, closer to a focused developer tool than a sci-fi operations console.
- **Core principles:** familiar before novel; evidence before claims; progressive disclosure; visible human/security boundaries.
- **Color philosophy:** paper-like neutral surfaces support long reading; deep ink anchors hierarchy; a restrained OAE teal marks the primary action and successful evidence; amber/red signal attention and failure only.
- **Layout paradigm:** stable workspace navigation beside a wide, task-focused content pane; the first-run screen is a focused sign-in/create choice, not a modal over an unexplained dashboard.
- **Signature elements:** OAE ring/branch mark; compact lifecycle labels; repository evidence summaries that open into raw JSON only when requested.
- **Interaction philosophy:** familiar click targets and form controls, keyboard-friendly labels, inline validation, and no hidden primary workflow.
- **Animation:** short, restrained transitions for navigation and disclosure only; respect reduced-motion preferences; never animate operational status as decoration.
- **Typography:** system sans-serif for UI, system monospace for IDs and raw evidence; clear heading/body/label hierarchy without tiny all-caps as the default.
- **Brand essence:** a governed workspace that helps software teams understand repository work and trust the evidence; **measured, candid, capable**.
- **Brand voice:** direct, calm, specific. Examples: “Start with a repository you can inspect.” “Your key is shown once; save it before you continue.”
- **Wordmark/mark:** OAE wordmark paired with a custom CSS ring-and-branch motif suggesting a repository and a controlled path, not a generic bot.
- **Signature brand color:** OAE teal, used sparingly for primary actions and verified success.

## Product behavior and boundaries

- First-run users can create a workspace or provide an existing API key.
- Workspace creation returns a one-time API key. Explain that it cannot be recovered, provide copy feedback, and make explicit that the browser remembers the key on this device when the user continues.
- The public beta's guided UI launches **Analyze** for one public GitHub repository with the API payload `{"operation":"analyze","payload":{"repository_url":"https://github.com/owner/repository"}}`.
- The UI polls the job endpoint and keeps the mission available in history if the user leaves or refreshes.
- Completed analyses explain repository facts that OAE actually returns (for example identity, branch, file counts and test counts). The full result remains available as expandable evidence.
- Show operation limits honestly: public beta analysis is read-oriented; no arbitrary shell execution, repository mutation, or automatic publishing is offered in the guided flow.
- Do not label the backend “nominal” or imply a check has run unless the UI has evidence from a real request.

## Implementation structure

- `frontend/index.html`: semantic shell, onboarding, workspace panes and accessible controls.
- `frontend/app.css`: responsive visual system, workspace layout, status, focus and motion rules.
- `frontend/app.js`: API client, workspace authentication, mission submission/polling, safe rendering and history views.
- `src/oae/api/app.py`: serve the HTML and same-origin frontend assets without changing API behavior.
- `tests/test_api.py`: check page/asset delivery; focused UI contract tests ensure the first-run and mission language continues to match the beta.
- `README.md` and `docs/BETA_DEVELOPER_GUIDE.md`: align first-run guidance with the actual interface and operation boundary.

## Scope discipline

This pass makes the existing controlled beta independently understandable and usable. It does not claim or introduce autonomous code changes, private-repository access, new authorization modes, a new backend service, production deployment, or a visual redesign of every internal subsystem.