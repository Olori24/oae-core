from oae.core.autonomous_queue_processor import AutonomousQueueProcessor


def test_creation():
    processor = AutonomousQueueProcessor()

    assert processor is not None


def test_register():
    processor = AutonomousQueueProcessor()

    processor.register("Backend Engineer")

    processor.submit("Authentication", 5)

    result = processor.process_next()

    assert result["engineer"] == "Backend Engineer"


def test_priority():
    processor = AutonomousQueueProcessor()

    processor.register("Backend Engineer")

    processor.submit("Low", 1)
    processor.submit("High", 10)

    result = processor.process_next()

    assert result["mission"] == "High"


def test_empty_queue():
    processor = AutonomousQueueProcessor()

    assert processor.process_next() is None


def test_multiple_processing():
    processor = AutonomousQueueProcessor()

    processor.register("Backend Engineer")

    processor.submit("One", 1)
    processor.submit("Two", 2)

    first = processor.process_next()
    second = processor.process_next()

    assert first["mission"] == "Two"
    assert second["mission"] == "One"