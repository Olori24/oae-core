
from oae.core.persistent_memory import PersistentMemory


def test_memory_creation(tmp_path):
    memory = PersistentMemory(tmp_path / "memory.json")

    assert memory is not None


def test_save_and_load(tmp_path):
    path = tmp_path / "memory.json"

    memory = PersistentMemory(path)

    memory.write(
        "Architect",
        "architecture.jwt",
        "Use JWT authentication",
    )

    memory.save()

    loaded = PersistentMemory(path)

    entry = loaded.read("architecture.jwt")

    assert entry.value == "Use JWT authentication"


def test_author_persisted(tmp_path):
    path = tmp_path / "memory.json"

    memory = PersistentMemory(path)

    memory.write(
        "QA",
        "qa.plan",
        "Run regression",
    )

    memory.save()

    loaded = PersistentMemory(path)

    assert loaded.read("qa.plan").author == "QA"


def test_exists_after_reload(tmp_path):
    path = tmp_path / "memory.json"

    memory = PersistentMemory(path)

    memory.write(
        "Security",
        "security.policy",
        "Require approval",
    )

    memory.save()

    loaded = PersistentMemory(path)

    assert loaded.exists("security.policy")


def test_keys_after_reload(tmp_path):
    path = tmp_path / "memory.json"

    memory = PersistentMemory(path)

    memory.write(
        "DevOps",
        "deploy",
        "Production",
    )

    memory.save()

    loaded = PersistentMemory(path)

    assert "deploy" in loaded.keys()