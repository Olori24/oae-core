from oae.core.autonomous_queue_processor import (
    AutonomousQueueProcessor,
)


class ContinuousEngineeringLoop:
    """
    Runs the autonomous engineering loop.
    """

    def __init__(self):
        self.processor = AutonomousQueueProcessor()

    def register(self, agent):
        self.processor.register(agent)

    def submit(self, mission, priority=0):
        self.processor.submit(mission, priority)

    def cycle(self):
        return self.processor.process_next()

    def run(self):
        results = []

        while True:
            result = self.cycle()

            if result is None:
                break

            results.append(result)

        return results