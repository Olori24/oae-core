"""
Kernel Boot Manager.
"""


class BootManager:
    """Coordinates subsystem startup."""

    def __init__(self, registry, event_bus):
        self.registry = registry
        self.event_bus = event_bus

    def validate_dependencies(self):

        available = {
            subsystem.name
            for subsystem in self.registry.all()
        }

        for subsystem in self.registry.all():
            for dependency in subsystem.dependencies:
                if dependency not in available:
                    raise RuntimeError(
                        f"{subsystem.name} requires '{dependency}'."
                    )

    def initialize(self):

        self.event_bus.publish("SYSTEM_STARTING")

        self.validate_dependencies()

        for subsystem in self.registry.all():
            subsystem.initialize()

        self.event_bus.publish("SYSTEM_READY")
