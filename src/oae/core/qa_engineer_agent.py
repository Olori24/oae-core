from dataclasses import dataclass

from oae.core.backend_engineer_agent import BackendTask


@dataclass
class QAReport:
    objective: str
    tests_to_run: list[str]


class QAEngineerAgent:
    """
    QA Engineer responsible for validating backend work.
    """

    def validate(self, task: BackendTask) -> QAReport:
        tests = [
            "Run unit tests",
            "Run integration tests",
            "Run regression tests",
            "Verify implementation",
        ]

        return QAReport(
            objective=task.objective,
            tests_to_run=tests,
        )