from oae.core.agent_capability import AgentCapabilityEngine


class AgentSelector:
    """
    Selects the most suitable agent for a capability.
    """

    def __init__(self):
        self.engine = AgentCapabilityEngine()

    def register_agent(self, name: str, capabilities: list[str]):
        self.engine.register(name, capabilities)

    def select(self, capability: str):
        matches = self.engine.find(capability)

        if not matches:
            return None

        return matches[0]