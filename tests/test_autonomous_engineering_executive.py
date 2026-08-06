from oae.core.autonomous_engineering_executive import (
    AutonomousEngineeringExecutive,
)


FILES = {
    "auth.py": """
import os

class Auth:
    pass

def login():
    pass
"""
}


def test_creation():
    executive = AutonomousEngineeringExecutive()

    assert executive is not None


def test_execute():
    executive = AutonomousEngineeringExecutive()

    result = executive.execute(FILES)

    assert len(result) == 1


def test_engineer_present():
    executive = AutonomousEngineeringExecutive()

    result = executive.execute(FILES)

    assert result[0]["engineer"] == "Backend Engineer"


def test_decision_present():
    executive = AutonomousEngineeringExecutive()

    result = executive.execute(FILES)

    assert "decision" in result[0]


def test_journal_updated():
    executive = AutonomousEngineeringExecutive()

    executive.execute(FILES)

    assert executive.journal.total() == 1