from oae.core.shared_agent_memory import SharedAgentMemory


def test_memory_creation():
    memory = SharedAgentMemory()

    assert memory is not None


def test_write_memory():
    memory = SharedAgentMemory()

    memory.write(
        "Architect",
        "architecture.jwt",
        "Use JWT authentication",
    )

    assert memory.exists("architecture.jwt")


def test_read_memory():
    memory = SharedAgentMemory()

    memory.write(
        "Architect",
        "architecture.jwt",
        "Use JWT authentication",
    )

    entry = memory.read("architecture.jwt")

    assert entry.value == "Use JWT authentication"


def test_author():
    memory = SharedAgentMemory()

    memory.write(
        "Architect",
        "architecture.jwt",
        "Use JWT authentication",
    )

    entry = memory.read("architecture.jwt")

    assert entry.author == "Architect"


def test_memory_keys():
    memory = SharedAgentMemory()

    memory.write("QA", "qa.plan", "Run full regression")

    assert len(memory.keys()) == 1