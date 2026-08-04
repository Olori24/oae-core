from oae.core.oae import OAE
from oae.core.context import EngineeringContext
from oae.core.stage_registry import StageRegistry
from oae.core.pipeline import EngineeringPipeline
from oae.core.stage import Stage
from oae.stages.verification_stage import VerificationStage
from oae.stages.audit_stage import AuditStage


class FailingStage(Stage):

    name = "Failing"

    def execute(self, context):
        raise RuntimeError("Intentional failure")


def test_pipeline_creation():
    oae = OAE()
    assert oae is not None
    assert oae.pipeline is not None


def test_engineering_context():
    context = EngineeringContext("Mission 020")

    assert context.mission == "Mission 020"
    assert context.status == "RUNNING"
    assert context.success is True
    assert context.execution_history == []
    assert context.audit == []
    assert context.warnings == []
    assert context.artifacts == []


def test_pipeline_has_stages():
    oae = OAE()
    assert len(oae.pipeline.stages) == 4


def test_stage_registry():
    registry = StageRegistry()
    assert len(registry.load()) == 4


def test_verification_stage():
    context = EngineeringContext("Mission")

    context.metadata["builder_completed"] = True

    result = VerificationStage().execute(context)

    assert result.metadata["verification_passed"] is True


def test_execution_history():
    context = EngineeringContext("Mission")

    context.record("Security", "started")
    context.record("Security", "completed")

    assert len(context.execution_history) == 2


def test_audit_stage():
    context = EngineeringContext("Mission")

    result = AuditStage().execute(context)

    assert len(result.audit) == 1


def test_pipeline_failure():

    pipeline = EngineeringPipeline()

    pipeline.stages = [FailingStage()]

    result = pipeline.execute("Mission Failure")

    assert result.success is False
    assert result.status == "FAILED"
    assert result.failed_stage == "Failing"
    assert result.error == "Intentional failure"


def test_context_complete():

    context = EngineeringContext("Mission")

    context.complete()

    assert context.status == "SUCCESS"
    assert context.duration is not None
