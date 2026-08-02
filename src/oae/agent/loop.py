from .agent import Agent


class AgentLoop:

    def __init__(self):
        self.agent = Agent()

    def run(self, goal):

        return self.agent.run(goal)
