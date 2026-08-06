from oae.core.repository_intelligence_builder import (
    RepositoryIntelligenceBuilder,
)
from oae.core.repository_diagnosis_v2 import (
    RepositoryDiagnosisV2,
)
from oae.core.engineering_analysis_engine import (
    EngineeringAnalysisEngine,
)
from oae.core.engineering_recommendation_engine import (
    EngineeringRecommendationEngine,
)
from oae.core.repository_recovery_engine import (
    RepositoryRecoveryEngine,
)


class EngineeringExecutivePipeline:
    """
    End-to-end autonomous engineering pipeline.
    """

    def __init__(self):
        self.builder = RepositoryIntelligenceBuilder()
        self.diagnosis = RepositoryDiagnosisV2()
        self.analysis = EngineeringAnalysisEngine()
        self.recommendation = EngineeringRecommendationEngine()
        self.recovery = RepositoryRecoveryEngine()

    def execute(self, repository_path):
        intelligence = self.builder.build(repository_path)

        diagnosis = self.diagnosis.diagnose(intelligence)

        analysis = self.analysis.analyze(
            intelligence["knowledge"]
        )

        recommendations = self.recommendation.recommend(
            analysis
        )

        recovery = self.recovery.recover(
            recommendations
        )

        return {
            "diagnosis": diagnosis,
            "analysis": analysis,
            "recommendations": recommendations,
            "recovery": recovery,
        }
