from oae.core.workload_manager import WorkloadManager


def test_manager_creation():
    manager = WorkloadManager()

    assert manager is not None


def test_register():
    manager = WorkloadManager()

    manager.register("Backend Engineer")

    assert manager.workload("Backend Engineer") == 0


def test_assign():
    manager = WorkloadManager()

    manager.assign("Backend Engineer")

    assert manager.workload("Backend Engineer") == 1


def test_complete():
    manager = WorkloadManager()

    manager.assign("Backend Engineer")
    manager.complete("Backend Engineer")

    assert manager.workload("Backend Engineer") == 0


def test_least_busy():
    manager = WorkloadManager()

    manager.assign("Backend Engineer")

    manager.register("QA Engineer")

    assert manager.least_busy() == "QA Engineer"