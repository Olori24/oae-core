from dataclasses import dataclass


@dataclass
class ClassifiedDependency:
    name: str
    category: str


class DependencyClassifier:
    """
    Categorizes software dependencies.
    """

    CATEGORIES = {
        "fastapi": "Web",
        "flask": "Web",
        "django": "Web",
        "sqlalchemy": "Database",
        "psycopg2": "Database",
        "pytest": "Testing",
        "openai": "AI",
        "anthropic": "AI",
        "langchain": "AI",
        "docker": "DevOps",
    }

    def classify(self, dependency: str) -> ClassifiedDependency:
        key = dependency.lower().split("==")[0]

        category = self.CATEGORIES.get(
            key,
            "Other",
        )

        return ClassifiedDependency(
            name=dependency,
            category=category,
        )