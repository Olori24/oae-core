from pathlib import Path


class SemanticRepositoryAnalyzer:
    """
    Performs semantic engineering analysis.
    """

    def analyze(self, root):

        root = Path(root)

        findings = []

        if (root / "src").exists():

            if not (
                root / "src"
                / "logging.py"
            ).exists():

                findings.append(
                    (
                        "Logging",
                        "Structured logging not detected.",
                        1,
                    )
                )

            if not (
                root / "src"
                / "config.py"
            ).exists():

                findings.append(
                    (
                        "Configuration",
                        "Central configuration missing.",
                        1,
                    )
                )

            if not (
                root / "src"
                / "middleware"
            ).exists():

                findings.append(
                    (
                        "Middleware",
                        "Middleware layer not detected.",
                        2,
                    )
                )

        return findings
