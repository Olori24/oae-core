class MessageBus:

    def __init__(self):
        self.messages = []

    def publish(self, sender, receiver, message):

        self.messages.append(
            {
                "sender": sender,
                "receiver": receiver,
                "message": message,
            }
        )

    def receive(self, receiver):

        inbox = []

        remaining = []

        for msg in self.messages:

            if msg["receiver"] == receiver:
                inbox.append(msg)
            else:
                remaining.append(msg)

        self.messages = remaining

        return inbox
