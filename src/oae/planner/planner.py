"""
OAE Planner.
"""

from oae.repository import RepositoryInspector

from .plan import Plan


class Planner:

    def __init__(self):

        self.inspector = RepositoryInspector()

    def create_plan(self, mission, root="."):

        profile = self.inspector.inspect(root)

        plan = Plan(mission)

        plan.profile = profile

        plan.add("Analyze mission")
        plan.add("Inspect repository")
        plan.add("Identify dependencies")
        plan.add("Generate implementation strategy")
        plan.add("Execute engineering pipeline")
        plan.add("Verify results")

        return plan
