from oae.core.engineering_journal import EngineeringJournal


def test_creation():
    journal = EngineeringJournal()

    assert journal is not None


def test_empty():
    journal = EngineeringJournal()

    assert journal.total() == 0
    assert journal.latest() is None


def test_record():
    journal = EngineeringJournal()

    journal.record(
        mission="Fix auth",
        engineer="Security Engineer",
        outcome="Success",
    )

    assert journal.total() == 1


def test_latest():
    journal = EngineeringJournal()

    journal.record(
        mission="Fix auth",
        engineer="Security Engineer",
        outcome="Success",
    )

    latest = journal.latest()

    assert latest["mission"] == "Fix auth"
    assert latest["engineer"] == "Security Engineer"


def test_entries():
    journal = EngineeringJournal()

    journal.record(
        mission="Mission A",
        engineer="Backend Engineer",
        outcome="Success",
    )

    journal.record(
        mission="Mission B",
        engineer="QA Engineer",
        outcome="Success",
    )

    assert len(journal.entries()) == 2


def test_confidence():
    journal = EngineeringJournal()

    journal.record(
        mission="Improve tests",
        engineer="QA Engineer",
        outcome="Success",
        confidence=0.98,
    )

    assert journal.latest()["confidence"] == 0.98