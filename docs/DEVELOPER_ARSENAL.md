# Developer Arsenal

OAE Core uses the Developer Arsenal as an engineering reuse and decision system. It is not a bookmark list.

## Mission
Reduce engineering cost and delivery time while increasing security, reliability, quality, and client value.

## Layers
- UI and design systems
- APIs and integrations
- Backend primitives
- AI engineering
- Automation and workers
- Security and supply chain
- Testing and quality
- DevOps and infrastructure
- Data and observability
- Documentation and delivery
- Africa/Nigeria adapters

## Adoption
1. Check existing OAE capability first.
2. Search for maintained reusable options.
3. Review license compatibility before code reuse.
4. Review security, maintenance, documentation, maturity, integration fit, operational complexity, cost, and exit path.
5. Isolate replaceable providers behind interfaces.
6. Add tests and operational documentation.
7. Record material architectural decisions.

## Scoring bands
- 90–100: production arsenal
- 75–89: approved
- 60–74: selective/reference
- Below 60: do not introduce without explicit review

## Non-negotiables
- OAE domain IP remains OAE IP.
- License before code reuse.
- Security before convenience.
- AI recommendations never bypass deterministic authorization or validation.
- Automation mutations are idempotent and auditable.
- Tenant/workspace scope is explicit.
- Cost and recovery are engineering requirements.
- Do not claim capacity, reliability, or production readiness without measured evidence.

## Definition of Done
Where applicable: authorization, tenant isolation, validation, audit semantics, deterministic failures, idempotency, tests, security scanning, migration/recovery planning, performance evidence, accessibility/responsive UX, operator docs, and provider/cost implications.

## Priority order
1. Security and supply chain
2. Testing confidence
3. Observability
4. Performance and capacity evidence
5. Reusable UI/data primitives
6. Worker/automation infrastructure
7. AI engineering
8. Africa/Nigeria adapters
9. Client delivery evidence

## Evidence rule
Keep IMPLEMENTED, TESTED, PUSHED, DEPLOYED, and VERIFIED IN PRODUCTION distinct. Keep MEASURED, ESTIMATED, UNKNOWN, PASS, FAIL, and BLOCKED distinct. Never manufacture evidence.