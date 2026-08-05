from dataclasses import dataclass

from oae.core.agent_bus import AgentBus, AgentMessage


@dataclass
class CollaborationResult:
    sender: str
    recipient: str
    subject: str
    delivered: bool


class AgentCollaboration:
    """
    Coordinates collaboration between AI engineering agents.
    """

    def __init__(self):
        self.bus = AgentBus()

    def delegate(
        self,
        sender: str,
        recipient: str,
        subject: str,
        payload: dict | None = None,
    ) -> CollaborationResult:

        self.bus.send(
            AgentMessage(
                sender=sender,
                recipient=recipient,
                subject=subject,
                payload=payload or {},
            )
        )

        return CollaborationResult(
            sender=sender,
            recipient=recipient,
            subject=subject,
            delivered=True,
        )