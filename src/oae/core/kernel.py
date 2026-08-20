
"""
OAE Kernel.
"""

from oae.core.boot_manager import BootManager
from oae.core.event_bus import EventBus
from oae.core.execution_engine import ExecutionEngine
from oae.core.oae import OAE
from oae.core.registry import SubsystemRegistry
from oae.governance.engine import GovernanceEngine


class Kernel:

    VERSION = "0.3.0-alpha"

    def __init__(self):

        self.events = EventBus()
        self.registry = SubsystemRegistry()

        self.registry.register(GovernanceEngine())

        self.boot = BootManager(
            self.registry,
            self.events,
        )

        self.oae = OAE()

        self.execution = ExecutionEngine(
            self.events,
            self.oae.pipeline,
        )

    def validate_dependencies(self):
        return self.boot.validate_dependencies()

    def initialize(self):
        return self.boot.initialize()

    def execute(self, mission):
        return self.execution.execute(mission)

    def ready(self):

        return all(
            subsystem.ready()
            for subsystem in self.registry.all()
        )

    def shutdown(self):

        self.events.publish("SYSTEM_SHUTDOWN")

        for subsystem in reversed(self.registry.all()):
            subsystem.shutdown()

    def info(self):

        return {
            "version": self.VERSION,
            "subsystems": len(self.registry.all()),
            "healthy": self.ready(),
        }

    def status(self):

        return {
            subsystem.name: subsystem.ready()
            for subsystem in self.registry.all()
        }

    def health(self):

        return {
            "kernel": self.ready(),
            "version": self.VERSION,
            "subsystems": self.status(),
            "healthy_subsystems": sum(
                subsystem.ready()
                for subsystem in self.registry.all()
            ),
            "total_subsystems": len(self.registry.all()),
        }

