from oae.core.event_bus import EventBus
from oae.core.execution_engine import ExecutionEngine


class DummyPipeline:

    def execute(self, context):
        context.success = True
        return context


def test_execution_history():

    engine = ExecutionEngine(
        EventBus(),
        DummyPipeline(),
    )

    engine.execute("Mission History")

    assert engine.history.count() == 1
    assert engine.history.all()[0]["mission"] == "Mission History"
    assert engine.history.all()[0]["success"] is True
