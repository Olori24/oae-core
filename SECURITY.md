# Security Policy

## Automated checks

The `Security` workflow runs dependency auditing, secret scanning, and supply-chain posture checks on pull requests, pushes to `main`, manual dispatches, and every Monday at 05:23 UTC. A failed security check must be investigated before merge.

## Reporting a vulnerability

Do not open a public issue for a suspected exploitable vulnerability. Use GitHub's private security advisory reporting for this repository when available, or contact the repository owner privately with the affected version, reproduction details, and impact assessment.

## Response expectations

Critical findings should be triaged within 24 hours and high-severity findings within seven days. Any exception requires an owner, an expiry date, and a documented compensating control.
