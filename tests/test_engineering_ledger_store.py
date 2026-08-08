from oae.core.engineering_ledger import LedgerEntry
from oae.core.engineering_ledger_store import EngineeringLedgerStore


def test_creation(tmp_path):
    store = EngineeringLedgerStore(tmp_path / "ledger.json")
    assert store is not None


def test_save_and_load(tmp_path):
    store = EngineeringLedgerStore(tmp_path / "ledger.json")

    entries = [
        LedgerEntry(
            timestamp="2026-08-07T10:00:00+00:00",
            event="MISSION_COMPLETED",
            details="Authentication implemented",
        )
    ]

    store.save(entries)

    loaded = store.load()

    assert loaded[0]["timestamp"] == "2026-08-07T10:00:00+00:00"
    assert loaded[0]["event"] == "MISSION_COMPLETED"
    assert loaded[0]["details"] == "Authentication implemented"


def test_missing_file_returns_empty(tmp_path):
    store = EngineeringLedgerStore(tmp_path / "missing.json")

    assert store.load() == []


def test_multiple_entries(tmp_path):
    store = EngineeringLedgerStore(tmp_path / "ledger.json")

    entries = [
        LedgerEntry("t1", "MISSION_STARTED", "Auth"),
        LedgerEntry("t2", "MISSION_COMPLETED", "Auth passed"),
    ]

    store.save(entries)

    loaded = store.load()

    assert len(loaded) == 2
    assert loaded[0]["event"] == "MISSION_STARTED"
    assert loaded[1]["event"] == "MISSION_COMPLETED"
