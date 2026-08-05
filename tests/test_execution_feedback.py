from oae.core.execution_feedback import ExecutionFeedback


def test_creation():
    feedback = ExecutionFeedback()

    assert feedback is not None


def test_register():
    feedback = ExecutionFeedback()

    feedback.register("Backend Engineer")

    assert feedback.workload("Backend Engineer") == 0


def test_assign():
    feedback = ExecutionFeedback()

    feedback.register("Backend Engineer")

    feedback.assign("Backend Engineer")

    assert feedback.workload("Backend Engineer") == 1


def test_complete():
    feedback = ExecutionFeedback()

    feedback.register("Backend Engineer")

    feedback.assign("Backend Engineer")

    feedback.complete("Backend Engineer")

    assert feedback.workload("Backend Engineer") == 0


def test_complete_empty():
    feedback = ExecutionFeedback()

    feedback.register("Backend Engineer")

    feedback.complete("Backend Engineer")

    assert feedback.workload("Backend Engineer") == 0