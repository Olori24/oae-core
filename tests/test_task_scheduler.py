from oae.core.task_scheduler import TaskScheduler


def test_scheduler_creation():
    scheduler = TaskScheduler()

    assert scheduler is not None


def test_schedule_task():
    scheduler = TaskScheduler()

    task = scheduler.schedule(
        "Backend Engineer",
        "Implement JWT",
    )

    assert task.agent == "Backend Engineer"
    assert task.task == "Implement JWT"


def test_pending_tasks():
    scheduler = TaskScheduler()

    scheduler.schedule(
        "QA Engineer",
        "Run Tests",
    )

    assert len(scheduler.pending()) == 1


def test_complete_task():
    scheduler = TaskScheduler()

    task = scheduler.schedule(
        "Security Engineer",
        "Review Authentication",
    )

    scheduler.complete(task)

    assert task.completed is True


def test_completed_tasks():
    scheduler = TaskScheduler()

    task = scheduler.schedule(
        "DevOps Engineer",
        "Deploy Release",
    )

    scheduler.complete(task)

    assert len(scheduler.completed()) == 1