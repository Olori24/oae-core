class Architect:

    def plan(self, mission):

        mission = mission.lower()

        if mission == "security":

            return [
                "__init__.py",
                "approvals.py",
                "audit.py",
                "permissions.py",
                "policies.py",
                "sandbox.py",
                "secrets.py",
            ]

        if mission == "git":

            return [
                "__init__.py",
                "branch.py",
                "status.py",
                "history.py",
                "diff.py",
                "commit.py",
            ]

        return [
            "__init__.py",
            f"{mission}.py",
        ]
