from oae.core.agent_collaboration import AgentCollaboration


def test_collaboration_creation():
    collaboration = AgentCollaboration()

    assert collaboration is not None


def test_delegate():
    collaboration = AgentCollaboration()

    result = collaboration.delegate(
        sender="Architect",
        recipient="Backend",
        subject="Implement Authentication",
    )

    assert result.delivered is True


def test_delegate_sender():
    collaboration = AgentCollaboration()

    result = collaboration.delegate(
        sender="Architect",
        recipient="Backend",
        subject="Task",
    )

    assert result.sender == "Architect"


def test_delegate_recipient():
    collaboration = AgentCollaboration()

    result = collaboration.delegate(
        sender="Architect",
        recipient="Backend",
        subject="Task",
    )

    assert result.recipient == "Backend"


def test_bus_receives_message():
    collaboration = AgentCollaboration()

    collaboration.delegate(
        sender="Architect",
        recipient="Backend",
        subject="Task",
    )

    inbox = collaboration.bus.inbox("Backend")

    assert len(inbox) == 1