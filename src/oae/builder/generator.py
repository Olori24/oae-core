from pathlib import Path

from .templates import MODULE_TEMPLATE


class Generator:

    def create(self, module_name, files):

        base = Path("src/oae")

        module = base / module_name

        module.mkdir(parents=True, exist_ok=True)

        for filename in files:

            path = module / filename

            if filename == "__init__.py":
                path.touch(exist_ok=True)
                continue

            classname = filename.replace(".py", "").capitalize()

            code = MODULE_TEMPLATE.format(
                name=filename.replace(".py", ""),
                classname=classname,
            )

            path.write_text(code)

        return module
