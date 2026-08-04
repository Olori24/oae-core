from oae.core.engineering_ledger import EngineeringLedger


def test_new_ledger_is_empty():
    ledger = EngineeringLedger()

    assert ledger.count() == 0
    assert ledger.entries() == []


def test_record_adds_entry():
    ledger = EngineeringLedger()

    ledger.record(
        "MISSION_STARTED",
        "Mission 076",
    )

    assert ledger.count() == 1

    entry = ledger.entries()[0]

    assert entry.event == "MISSION_STARTED"
    assert entry.details == "Mission 076"
    assert entry.timestamp is not None