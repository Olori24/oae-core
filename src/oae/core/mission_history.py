from oae.core.execution_outcome_analyzer import ExecutionOutcomeAnalyzer

"""
Mission execution history.
"""


class MissionHistory:

    def __init__(self):
        self._history = []

    def record(self, context):

        self._history.append({
            "mission": context.mission,
            "success": context.success,
        })

    def all(self):
        return list(self._history)

    def count(self):
        return len(self._history)

    def analyze(self):
        analyzer = ExecutionOutcomeAnalyzer()
        return analyzer.analyze(self._history)
