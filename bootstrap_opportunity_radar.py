from pathlib import Path

from oae.core.project_specification import ProjectSpecification
from oae.core.project_bootstrap_orchestrator import (
    ProjectBootstrapOrchestrator,
)

ROOT = Path(
    "/data/data/com.termux/files/home/oae-core/sandbox/opportunity-radar-africa"
)

spec = ProjectSpecification(
    name="Opportunity Radar Africa",
    description="AI-powered platform for discovering grants, jobs, scholarships, fellowships and startup opportunities across Africa.",
    language="Python",
    framework="FastAPI",
    database="PostgreSQL",
    testing_framework="pytest",
)

orchestrator = ProjectBootstrapOrchestrator()

orchestrator.bootstrap(ROOT, spec)

print("✅ Repository successfully bootstrapped.")
