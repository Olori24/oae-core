"""
Stage Registry.

Maintains the ordered list of pipeline stages.
"""

from oae.stages.security_stage import SecurityStage
from oae.stages.builder_stage import BuilderStage
from oae.stages.verification_stage import VerificationStage
from oae.stages.audit_stage import AuditStage


class StageRegistry:
    """Registry for Engineering Pipeline stages."""

    def __init__(self):
        self._stages = []

        self.register(SecurityStage())
        self.register(BuilderStage())
        self.register(VerificationStage())
        self.register(AuditStage())

    def register(self, stage):
        self._stages.append(stage)

    def load(self):
        return list(self._stages)
