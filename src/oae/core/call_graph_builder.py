import ast


class CallGraphBuilder:
    """
    Builds a function call graph from Python source code.
    """

    def build(self, source_code: str):
        tree = ast.parse(source_code)

        graph: dict[str, list[str]] = {}
        current_function: str | None = None

        class Visitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                nonlocal current_function
                current_function = node.name
                graph.setdefault(current_function, [])
                self.generic_visit(node)

            def visit_Call(self, node):
                if current_function:
                    if isinstance(node.func, ast.Name):
                        graph[current_function].append(node.func.id)
                self.generic_visit(node)

        Visitor().visit(tree)

        return graph
