from oae.core.project_skeleton_generator import ProjectSkeletonGenerator
from oae.core.readme_generator import ReadmeGenerator
from oae.core.gitignore_generator import GitignoreGenerator
from oae.core.requirements_generator import RequirementsGenerator
from oae.core.env_generator import EnvGenerator
from oae.core.pyproject_generator import PyprojectGenerator
from oae.core.dockerfile_generator import DockerfileGenerator
from oae.core.github_actions_generator import GitHubActionsGenerator


class ProjectBootstrapOrchestrator:
    """
    Executes the complete repository bootstrap process.
    """

    def bootstrap(self, root, specification):
        ProjectSkeletonGenerator().generate(root, specification)
        ReadmeGenerator().generate(root, specification)
        GitignoreGenerator().generate(root)
        RequirementsGenerator().generate(root)
        EnvGenerator().generate(root)
        PyprojectGenerator().generate(root, specification)
        DockerfileGenerator().generate(root)
        GitHubActionsGenerator().generate(root)

        return True
