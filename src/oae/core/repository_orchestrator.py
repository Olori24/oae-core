from oae.core.repository_analyzer import RepositoryAnalyzer
from oae.core.repository_intelligence_engine import RepositoryIntelligenceEngine
from oae.core.intelligent_mission_generator import IntelligentMissionGenerator


class RepositoryOrchestrator:
    """
    End-to-end repository engineering orchestration.
    """

    def __init__(self):
        self.analyzer = RepositoryAnalyzer()
        self.intelligence = RepositoryIntelligenceEngine()
        self.generator = IntelligentMissionGenerator()

    def process(self, repository_profile):
        findings = self.analyzer.analyze(repository_profile)
        intelligence = self.intelligence.classify(findings)
        return self.generator.generate(intelligence)
