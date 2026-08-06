from oae.core.repository_intelligence_builder import RepositoryIntelligenceBuilder
from oae.core.repository_diagnosis_v2 import RepositoryDiagnosisV2
from oae.core.repository_backlog_generator import RepositoryBacklogGenerator


class EngineeringExecutivePipeline:
    """
    Complete repository engineering workflow.
    """

    def __init__(self):
        self.builder = RepositoryIntelligenceBuilder()
        self.diagnosis = RepositoryDiagnosisV2()
        self.backlog = RepositoryBacklogGenerator()

    def execute(self, repository_path):
        intelligence = self.builder.build(repository_path)

        diagnosis = self.diagnosis.diagnose(intelligence)

        missions = self.backlog.generate(diagnosis)

        return {
            "intelligence": intelligence,
            "diagnosis": diagnosis,
            "missions": missions,
        }
