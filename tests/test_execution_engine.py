from oae.core.event_bus import EventBus
from oae.core.execution_engine import ExecutionEngine


class DummyPipeline:

    def execute(self, context):
        return context


def test_execution_engine():

    bus = EventBus()

    pipeline = DummyPipeline()

    engine = ExecutionEngine(bus, pipeline)

    result = engine.execute("Mission 058")

    assert result.mission == "Mission 058"
