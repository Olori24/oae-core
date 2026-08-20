from oae.executor.engine import Executor
from oae.memory.store import MemoryStore
from oae.planner.planner import Planner
from oae.providers.manager import ProviderManager
from oae.repository.scanner import RepositoryScanner
from oae.verifier.verifier import Verifier

from .mission import Mission
from .state import AgentState


class Agent:

    def __init__(self):
        self.state = AgentState()
        self.planner = Planner()
        self.providers = ProviderManager()
        self.executor = Executor()
        self.memory = MemoryStore()
        self.verifier = Verifier()
        self.scanner = RepositoryScanner()

    def run(self, goal: str):

        mission = Mission(goal)

        print("\n========================================")
        print("Repository Report")
        print("========================================")

        report = self.scanner.scan()

        for key, value in report.items():
            print(f" • {key}: {value}")

        self.state.status = "planning"

        print("\nMission Plan:\n")

        tasks = self.planner.create_plan(goal)

        for task in tasks:
            print(f" • {task.description}")

        self.state.status = "routing"

        provider = self.providers.get()
        result = provider.generate(goal)

        self.state.status = "executing"

        self.executor.write_readme(goal)

        verified, message = self.verifier.verify_file("README.md")

        print(f"\nVerification: {message}")

        self.memory.save("repository_report", report)
        self.memory.save("last_mission", goal)
        self.memory.save("last_provider", provider.name)
        self.memory.save(
            "last_status",
            "completed" if verified else "failed"
        )

        self.state.status = "completed" if verified else "failed"

        mission.finish()

        return result
