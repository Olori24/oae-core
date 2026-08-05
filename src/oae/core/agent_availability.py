class AgentAvailability:
    """
    Tracks the availability state of engineers.
    """

    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

    def __init__(self):
        self._states = {}

    def register(self, agent):
        self._states[agent] = self.IDLE

    def set_state(self, agent, state):
        self._states[agent] = state

    def state(self, agent):
        return self._states.get(agent)

    def available(self, agent):
        return self.state(agent) == self.IDLE

    def agents(self):
        return list(self._states.keys())