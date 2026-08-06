from dataclasses import dataclass


@dataclass
class ProjectSpecification:
    """
    Defines the engineering requirements for a project.
    """

    name: str
    description: str
    language: str
    framework: str
    database: str
    testing_framework: str
    docker: bool = True
    ci: bool = True
