import json
from pathlib import Path


class ApiIntegrationGenerator:
    """Integrate generated API routers without coupling applications to a domain."""

    def generate(self, root, specification=None):
        root = Path(root)
        main = root / "src" / "main.py"
        if not main.exists():
            return

        title = getattr(specification, "name", None) or "Generated Application"
        api_dir = root / "src" / "api"
        routers = []
        if api_dir.exists():
            for module in sorted(api_dir.glob("*.py")):
                if module.name == "__init__.py":
                    continue
                routers.append(module.stem)

        imports = [
            "import sys",
            "from pathlib import Path",
            "",
            "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))",
            "",
            "from fastapi import FastAPI",
        ]
        includes = []
        for module in routers:
            imports.append(f"from src.api.{module} import router as {module}_router")
            includes.append(f"app.include_router({module}_router)")

        content = "\n".join(imports)
        content += f"\n\napp = FastAPI(title={json.dumps(title)})\n\n"
        if includes:
            content += "\n".join(includes) + "\n"
        content += "\nif __name__ == \"__main__\":\n    print(\"Generated application is healthy\")\n"
        main.write_text(content, encoding="utf-8")
