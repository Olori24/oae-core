from oae.core.agent_bus import AgentBus, AgentMessage


def test_bus_creation():
    bus = AgentBus()

    assert bus is not None


def test_send_message():
    bus = AgentBus()

    message = AgentMessage(
        sender="Architect",
        recipient="Backend",
        subject="Implement Feature",
    )

    bus.send(message)

    assert len(bus.messages) == 1


def test_inbox():
    bus = AgentBus()

    bus.send(
        AgentMessage(
            sender="Architect",
            recipient="Backend",
            subject="Task",
        )
    )

    inbox = bus.inbox("Backend")

    assert len(inbox) == 1
    assert inbox[0].sender == "Architect"


def test_sent_by():
    bus = AgentBus()

    bus.send(
        AgentMessage(
            sender="QA",
            recipient="Security",
            subject="Review",
        )
    )

    sent = bus.sent_by("QA")

    assert len(sent) == 1
    assert sent[0].recipient == "Security"


def test_multiple_messages():
    bus = AgentBus()

    bus.send(
        AgentMessage(
            sender="Architect",
            recipient="Backend",
            subject="Task 1",
        )
    )

    bus.send(
        AgentMessage(
            sender="Architect",
            recipient="QA",
            subject="Task 2",
        )
    )

    assert len(bus.sent_by("Architect")) == 2