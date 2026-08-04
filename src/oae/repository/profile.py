"""
Repository profile.
"""


class RepositoryProfile:

    def __init__(self):

        self.has_git = False
        self.has_readme = False
        self.has_pyproject = False
        self.uses_pytest = False

        self.language = None
        self.package_manager = None
        self.framework = None

    def summary(self):

        return {
            "language": self.language,
            "package_manager": self.package_manager,
            "framework": self.framework,
            "git": self.has_git,
            "pyproject": self.has_pyproject,
            "pytest": self.uses_pytest,
        }
