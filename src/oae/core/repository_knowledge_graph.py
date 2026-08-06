from oae.core.python_ast_parser import PythonASTParser


class RepositoryKnowledgeGraph:
    """
    Builds a knowledge graph for an entire repository.
    """

    def __init__(self):
        self.parser = PythonASTParser()

    def build(self, files):
        graph = {}

        for filename, source in files.items():
            tree = self.parser.parse(source)

            graph[filename] = {
                "classes": self.parser.classes(tree),
                "functions": self.parser.functions(tree),
                "imports": self.parser.imports(tree),
            }

        return graph
