import ast


class PythonASTParser:
    """
    Parses Python source code into an abstract syntax tree.
    """

    def parse(self, source_code: str):
        return ast.parse(source_code)

    def functions(self, tree):
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]

    def classes(self, tree):
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        ]

    def imports(self, tree):
        modules = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                modules.append(node.module)

        return [m for m in modules if m]