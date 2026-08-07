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


class ProjectBootstrapOrchestrator:
    """
    Executes the complete repository bootstrap process.
    """

    def bootstrap(self, root, specification):
        root = Path(root)

        ProjectSkeletonGenerator().generate(root, specification)

        ReadmeGenerator().generate(root, specification)

        GitignoreGenerator().generate(root)

        RequirementsGenerator().generate(root)

        EnvGenerator().generate(root)

        PyprojectGenerator().generate(root, specification)

        DockerfileGenerator().generate(root)

        GitHubActionsGenerator().generate(root)

        ApplicationScaffoldGenerator().generate(
            root,
            specification,
        )

        ExecutableApplicationGenerator().generate(
            root,
            specification,
        )

        DatabaseGenerator().generate(root)

        OpportunityModelGenerator().generate(root)

        OpportunityRepositoryGenerator().generate(root)

        OpportunityApiGenerator().generate(root)

        return root
