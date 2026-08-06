from oae.core.multi_agent_dispatcher import MultiAgentDispatcher


class AutonomousQueueProcessor:
    """
    Continuously processes engineering missions.
    """

    def __init__(self):
        self.dispatcher = MultiAgentDispatcher()

    def register(self, agent):
        self.dispatcher.register(agent)

    def submit(self, mission, priority=0):
        self.dispatcher.add_mission(mission, priority)

    def process_next(self):
        return self.dispatcher.dispatch()