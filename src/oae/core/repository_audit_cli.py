from pathlib import Path
from collections import Counter


class RepositoryAuditCLI:
    """
    Generates a multi-language engineering report for a repository.
    """

    def audit(self, repository_path):
        repo = Path(repository_path)

        files = [f for f in repo.rglob("*") if f.is_file()]

        extensions = Counter(f.suffix.lower() or "<no-extension>" for f in files)

        top_extensions = "\n".join(
            f"- {ext}: {count}"
            for ext, count in extensions.most_common(10)
        )

        report = f"""# OAE Engineering Report

Repository:
{repo.name}

Total Files:
{len(files)}

Top File Types:
{top_extensions}

Repository Status:
READY FOR ANALYSIS

Next Stage:
- Repository Intelligence
- Dependency Analysis
- Dead Code Detection
- Technical Debt Discovery
- Architecture Mapping
"""

        reports = repo / "reports"
        reports.mkdir(exist_ok=True)

        report_path = reports / "engineering_report.md"
        report_path.write_text(report)

        return {
            "status": "completed",
            "report": str(report_path),
        }
