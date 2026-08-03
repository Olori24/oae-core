from oae.core.oae import OAE
from oae.core.context import EngineeringContext
from oae.core.stage_registry import StageRegistry
from oae.stages.verification_stage import VerificationStage


def test_pipeline_creation():
    oae = OAE()
    assert oae is not None
    assert oae.pipeline is not None


def test_engineering_context():
    context = EngineeringContext("Mission 020")
    assert context.mission == "Mission 020"
    assert context.generated_files == []
    assert context.metadata == {}
    assert context.execution_history == []


def test_pipeline_has_stages():
    oae = OAE()
    assert len(oae.pipeline.stages) == 3


def test_stage_registry():
    registry = StageRegistry()
    assert len(registry.load()) == 3


def test_context_metadata():
    context = EngineeringContext("Mission")
    context.metadata["builder_completed"] = True
    assert context.metadata["builder_completed"] is True


def test_verification_stage():
    context = EngineeringContext("Mission")
    context.metadata["builder_completed"] = True

    stage = VerificationStage()
    result = stage.execute(context)

    assert result.metadata["verification_passed"] is True


def test_execution_history():
    context = EngineeringContext("Mission")

    context.record("Security", "started")
    context.record("Security", "completed")

    assert len(context.execution_history) == 2
