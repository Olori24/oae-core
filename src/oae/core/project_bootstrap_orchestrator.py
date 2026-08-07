from pathlib import Path

from oae.core.project_skeleton_generator import ProjectSkeletonGenerator
from oae.core.readme_generator import ReadmeGenerator
from oae.core.gitignore_generator import GitignoreGenerator
from oae.core.requirements_generator import RequirementsGenerator
from oae.core.env_generator import EnvGenerator
from oae.core.pyproject_generator import PyprojectGenerator
from oae.core.dockerfile_generator import DockerfileGenerator
from oae.core.github_actions_generator import GitHubActionsGenerator
from oae.core.application_scaffold_generator import ApplicationScaffoldGenerator
from oae.core.executable_application_generator import ExecutableApplicationGenerator
from oae.core.database_generator import DatabaseGenerator
from oae.core.opportunity_model_generator import OpportunityModelGenerator
from oae.core.opportunity_repository_generator import OpportunityRepositoryGenerator
from oae.core.opportunity_api_generator import OpportunityApiGenerator
from oae.core.authentication_generator import AuthenticationGenerator
from oae.core.api_integration_generator import ApiIntegrationGenerator


class ProjectBootstrapOrchestrator:

    def __init__(self):
        self.generators = [
            ProjectSkeletonGenerator(),
            ReadmeGenerator(),
            GitignoreGenerator(),
            RequirementsGenerator(),
            EnvGenerator(),
            PyprojectGenerator(),
            DockerfileGenerator(),
            GitHubActionsGenerator(),
            ApplicationScaffoldGenerator(),
            ExecutableApplicationGenerator(),
            DatabaseGenerator(),
            OpportunityModelGenerator(),
            OpportunityRepositoryGenerator(),
            OpportunityApiGenerator(),
            AuthenticationGenerator(),
            ApiIntegrationGenerator(),
        ]

    def bootstrap(self, root, specification):
        root = Path(root)

        for generator in self.generators:
            try:
                generator.generate(root, specification)
            except TypeError:
                generator.generate(root)

        return root
