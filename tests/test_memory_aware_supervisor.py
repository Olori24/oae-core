from oae.core.memory_aware_supervisor import MemoryAwareSupervisor


def test_supervisor_creation():
    supervisor = MemoryAwareSupervisor()

    assert supervisor is not None


def test_execute():
    supervisor = MemoryAwareSupervisor()

    result = supervisor.execute("Implement JWT")

    assert result.completed is True


def test_memory_written():
    supervisor = MemoryAwareSupervisor()

    supervisor.execute("Implement JWT")

    assert supervisor.memory.exists("mission:Implement JWT")


def test_memory_value():
    supervisor = MemoryAwareSupervisor()

    supervisor.execute("Implement JWT")

    entry = supervisor.memory.read("mission:Implement JWT")

    assert entry.value == "Mission Started"


def test_backend_received_task():
    supervisor = MemoryAwareSupervisor()

    supervisor.execute("Implement JWT")

    inbox = supervisor.collaboration.bus.inbox(
        "Backend Engineer"
    )

    assert len(inbox) == 1