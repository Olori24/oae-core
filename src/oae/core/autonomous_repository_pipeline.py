from oae.core.repository_analyzer import RepositoryAnalyzer
from oae.core.repository_intelligence_engine import (
    RepositoryIntelligenceEngine,
)
from oae.core.intelligent_mission_generator import (
    IntelligentMissionGenerator,
)


class AutonomousRepositoryPipeline:
    """
    Complete autonomous repository intelligence pipeline.
    """

    def __init__(self):
        self.analyzer = RepositoryAnalyzer()
        self.intelligence = RepositoryIntelligenceEngine()
        self.generator = IntelligentMissionGenerator()

    def process(self, repository_profile):
        findings = self.analyzer.analyze(repository_profile)
        intelligence = self.intelligence.classify(findings)
        missions = self.generator.generate(intelligence)

        return missions