"""
Kernel subsystem registry.
"""


class SubsystemRegistry:

    def __init__(self):
        self._subsystems = []

    def register(self, subsystem):
        self._subsystems.append(subsystem)

    def all(self):
        return list(self._subsystems)
