"""
Base subsystem class.
"""


class Subsystem:
    """Base class for kernel-managed subsystems."""

    name = "subsystem"
    dependencies: list[str] = []

    def __init__(self):
        self._initialized = False

    def initialize(self):
        self._initialized = True

    def ready(self):
        return self._initialized

    def shutdown(self):
        self._initialized = False
