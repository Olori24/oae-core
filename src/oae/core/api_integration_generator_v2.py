from pathlib import Path


class ApiIntegrationGeneratorV2:
    """Domain-agnostic API integration for generated applications."""

    def generate(self, root, specification=None):
        root = Path(root)
        main = root / "src" / "main.py"
        if not main.exists():
            return
        title = getattr(specification, "name", None) or "Generated Application"
        api_dir = root / "src" / "api"
        routers = sorted(
            module.stem for module in api_dir.glob("*.py")
            if module.name != "__init__.py"
        ) if api_dir.exists() else []
        imports = ["from fastapi import FastAPI"]
        includes = []
        for module in routers:
            imports.append(f"from src.api.{module} import router as {module}_router")
            includes.append(f"app.include_router({module}_router)")
        text = "\n".join(imports) + f"\n\napp = FastAPI(title={title!r})\n\n"
        if includes:
            text += "\n".join(includes) + "\n"
        main.write_text(text, encoding="utf-8")
