from pathlib import Path

from oae.capabilities.capability import Capability


class CapabilityDiscoveryEngine:
    """
    Discovers missing engineering capabilities
    from repository structure.
    """

    def discover(self, root):

        root = Path(root)

        capabilities = []

        if not (root / "Dockerfile").exists():
            capabilities.append(
                Capability(
                    "Docker",
                    "Repository has no Docker support.",
                    1,
                )
            )

        if not (root / ".github").exists():
            capabilities.append(
                Capability(
                    "CI/CD",
                    "Repository has no GitHub Actions.",
                    2,
                )
            )

        if not (root / "tests").exists():
            capabilities.append(
                Capability(
                    "Testing",
                    "Repository has no automated tests.",
                    1,
                )
            )

        if not (root / "README.md").exists():
            capabilities.append(
                Capability(
                    "Documentation",
                    "Repository has no README.",
                    3,
                )
            )

        return capabilities
