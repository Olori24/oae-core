from pathlib import Path
import subprocess


class RepositoryUpdateEngine:
    """
    Updates an existing Git repository.
    """

    def update(self, repository_path):
        repository_path = Path(repository_path)

        if not repository_path.exists():
            raise FileNotFoundError(repository_path)

        subprocess.run(
            [
                "git",
                "-C",
                str(repository_path),
                "pull",
                "--ff-only",
            ],
            check=True,
        )

        return repository_path
