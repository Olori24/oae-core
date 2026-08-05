from dataclasses import dataclass, field


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    subject: str
    payload: dict = field(default_factory=dict)


class AgentBus:
    """
    Communication bus for AI engineering agents.
    """

    def __init__(self):
        self.messages: list[AgentMessage] = []

    def send(self, message: AgentMessage):
        self.messages.append(message)

    def inbox(self, recipient: str):
        return [
            message
            for message in self.messages
            if message.recipient == recipient
        ]

    def sent_by(self, sender: str):
        return [
            message
            for message in self.messages
            if message.sender == sender
        ]