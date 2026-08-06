from pathlib import Path


class RepositoryIntelligenceReport:
    """
    Produces a high-level engineering summary of a repository.
    """

    def generate(self, repository_path):
        repo = Path(repository_path)

        source_files = [
            f for f in repo.rglob("*")
            if f.is_file() and ".git" not in str(f)
        ]

        test_files = [
            f for f in source_files
            if "tests" in str(f)
        ]

        python_files = [
            f for f in source_files
            if f.suffix == ".py"
        ]

        report = {
            "repository": repo.name,
            "total_files": len(source_files),
            "python_files": len(python_files),
            "test_files": len(test_files),
            "source_directory_exists": (repo / "src").exists(),
            "tests_directory_exists": (repo / "tests").exists(),
            "docs_directory_exists": (repo / "docs").exists(),
        }

        return report
