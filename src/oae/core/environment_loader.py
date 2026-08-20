from pathlib import Path


class EnvironmentLoader:
    """
    Loads simple KEY=VALUE pairs from a .env file.
    """

    def load(self, root):
        root = Path(root)

        env_file = root / ".env"

        values: dict[str, str] = {}

        if not env_file.exists():
            return values

        for line in env_file.read_text().splitlines():
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            values[key.strip()] = value.strip()

        return values
