from dataclasses import dataclass, field


@dataclass
class Node:
    name: str
    edges: list[str] = field(default_factory=list)


class KnowledgeGraph:
    """
    Represents relationships between repository components.
    """

    def __init__(self):
        self.nodes: dict[str, Node] = {}

    def add_node(self, name: str):
        if name not in self.nodes:
            self.nodes[name] = Node(name=name)

    def connect(self, source: str, target: str):
        self.add_node(source)
        self.add_node(target)

        if target not in self.nodes[source].edges:
            self.nodes[source].edges.append(target)

    def neighbors(self, node: str):
        if node not in self.nodes:
            return []

        return self.nodes[node].edges